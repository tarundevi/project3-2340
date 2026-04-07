import socket
import ssl
import re
import uuid
from io import BytesIO
from pathlib import Path
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi
from pypdf import PdfReader

from app.config import settings
from app.services.vectorstore import COLLECTION_NAME, get_client, get_collection
USER_AGENT = "NutriBot/1.0 (+frontend developer ingestion)"


class IngestionError(Exception):
    pass


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3", "h4"}:
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        if self._in_title:
            self._title_parts.append(cleaned)
        self._text_parts.append(cleaned)

    @property
    def title(self) -> str:
        return " ".join(self._title_parts).strip()

    @property
    def text(self) -> str:
        text = " ".join(self._text_parts)
        text = re.sub(r"\s*\n\s*", "\n", text)
        text = re.sub(r"\n{2,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()


def _clean_topic(topic: str) -> str:
    return topic.strip()


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            split_at = normalized.rfind(" ", start, end)
            if split_at > start + (chunk_size // 2):
                end = split_at
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(end - overlap, 0)
    return chunks


def _safe_title(title: str, fallback: str) -> str:
    cleaned = " ".join(title.split()).strip()
    return cleaned or fallback


def _decode_uploaded_file(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".markdown", ".json", ".csv", ".pdf"}:
        raise IngestionError("Unsupported file type. Upload .txt, .md, .json, .csv, or .pdf.")

    if suffix == ".pdf":
        try:
          reader = PdfReader(BytesIO(content))
        except Exception as exc:
          raise IngestionError("PDF could not be opened.") from exc

        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            page_text = page_text.strip()
            if page_text:
                pages.append(page_text)

        if not pages:
            raise IngestionError("PDF did not contain readable text.")

        return "\n\n".join(pages)

    try:
        raw_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IngestionError("File must be UTF-8 encoded.") from exc

    if suffix == ".json":
        try:
            parsed = __import__("json").loads(raw_text)
        except Exception as exc:
            raise IngestionError("JSON file could not be parsed.") from exc
        return __import__("json").dumps(parsed, indent=2, ensure_ascii=True)

    if suffix == ".csv":
        rows = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not rows:
            raise IngestionError("CSV file is empty.")
        return "\n".join(rows)

    return raw_text


def ingest_text_document(content: str, title: str, topic: str = "", url: str = "") -> dict:
    cleaned_content = content.strip()
    if not cleaned_content:
        raise IngestionError("Content cannot be empty.")

    document_title = _safe_title(title, "Untitled Document")
    chunks = _chunk_text(cleaned_content)
    if not chunks:
        raise IngestionError("Content could not be converted into document chunks.")

    topic_value = _clean_topic(topic)
    base_id = uuid.uuid4().hex
    collection = get_collection(create=True)

    collection.upsert(
        ids=[f"{base_id}-{index}" for index in range(len(chunks))],
        documents=chunks,
        metadatas=[
            {
                "title": document_title,
                "url": url.strip(),
                "topic": topic_value,
                "source": "manual",
                "chunk_index": str(index + 1),
            }
            for index in range(len(chunks))
        ],
    )

    return {
        "title": document_title,
        "url": url.strip(),
        "topic": topic_value,
        "chunk_count": len(chunks),
    }


def fetch_url_document(url: str) -> dict:
    request = Request(
        url.strip(),
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urlopen(request, timeout=15, context=ssl_context) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="ignore")
    except HTTPError as exc:
        raise IngestionError(f"Could not fetch URL ({exc.code}).") from exc
    except URLError as exc:
        reason = exc.reason
        if isinstance(reason, ssl.SSLCertVerificationError):
            raise IngestionError("Could not verify the website's SSL certificate.") from exc
        if isinstance(reason, socket.gaierror):
            raise IngestionError("Could not resolve the website domain name.") from exc
        raise IngestionError(f"Could not fetch URL: {reason}") from exc

    parser = _HTMLTextExtractor()
    parser.feed(html)

    title = _safe_title(parser.title, url)
    text = parser.text
    if not text:
        raise IngestionError("The URL did not contain readable text.")

    return {"title": title, "content": text, "url": url.strip()}


def ingest_url_document(url: str, topic: str = "") -> dict:
    fetched = fetch_url_document(url)
    return ingest_text_document(
        content=fetched["content"],
        title=fetched["title"],
        topic=topic,
        url=fetched["url"],
    )


def ingest_uploaded_file(filename: str, content: bytes, topic: str = "") -> dict:
    if not filename:
        raise IngestionError("A file name is required.")
    if not content:
        raise IngestionError("Uploaded file is empty.")

    text = _decode_uploaded_file(filename, content)
    title = Path(filename).stem.replace("_", " ").replace("-", " ").strip() or "Uploaded File"
    return ingest_text_document(content=text, title=title, topic=topic)


def get_collection_overview(limit: int = 20) -> dict:
    client = get_client()
    collections = {collection.name for collection in client.list_collections()}
    if COLLECTION_NAME not in collections:
        return {
            "collection_name": COLLECTION_NAME,
            "exists": False,
            "chunk_count": 0,
            "documents": [],
        }

    collection = get_collection(create=False)
    sample = collection.peek(limit=100)
    metadatas = sample.get("metadatas", []) or []
    seen: set[tuple[str, str, str]] = set()
    documents: list[dict] = []

    for metadata in metadatas:
        metadata = metadata or {}
        title = metadata.get("title") or "Untitled Document"
        url = metadata.get("url") or ""
        topic = metadata.get("topic") or ""
        key = (title, url, topic)
        if key in seen:
            continue
        seen.add(key)
        documents.append({"title": title, "url": url, "topic": topic})
        if len(documents) >= limit:
            break

    return {
        "collection_name": COLLECTION_NAME,
        "exists": True,
        "chunk_count": collection.count(),
        "documents": documents,
    }
