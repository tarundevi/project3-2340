import logging
import math
import re
from typing import TypedDict

from app.services.vectorstore import get_collection

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "an", "and", "are", "be", "by", "do", "for", "from", "help", "how",
    "i", "in", "is", "it", "me", "need", "of", "on", "or", "should", "tell",
    "the", "to", "what", "with", "you", "your",
}


class RetrievedSource(TypedDict):
    title: str
    url: str


class RetrievalResult(TypedDict):
    context: list[str]
    sources: list[RetrievedSource]


def _tokenize(text: str) -> list[str]:
    return [_normalize_token(token) for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS]


def _normalize_token(token: str) -> str:
    for suffix in ("ing", "ers", "er", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]
    return token


def _relevance_score(query: str, document: str, metadata: dict) -> int:
    query_token_list = _tokenize(query)
    query_tokens = set(query_token_list)
    if not query_tokens:
        return 0

    document_tokens = set(_tokenize(document))
    title_tokens = set(_tokenize(metadata.get("title", "")))

    overlap = len(query_tokens & document_tokens)
    title_overlap = len(query_tokens & title_tokens) * 2

    joined_query = " ".join(query_token_list)
    phrase_bonus = 0
    if joined_query and joined_query in document.lower():
        phrase_bonus += 4
    if joined_query and joined_query in metadata.get("title", "").lower():
        phrase_bonus += 5

    query_bigrams = {
        " ".join(pair)
        for pair in zip(query_token_list, query_token_list[1:])
    }
    document_lower = document.lower()
    title_lower = metadata.get("title", "").lower()
    bigram_bonus = sum(2 for bigram in query_bigrams if bigram in document_lower)
    bigram_bonus += sum(3 for bigram in query_bigrams if bigram in title_lower)

    return overlap + title_overlap + phrase_bonus + bigram_bonus


def _coverage_count(query: str, document: str, metadata: dict) -> int:
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return 0

    combined_tokens = set(_tokenize(document)) | set(_tokenize(metadata.get("title", "")))
    return len(query_tokens & combined_tokens)


def _source_title(metadata: dict, document: str, index: int) -> str:
    return (
        metadata.get("title")
        or metadata.get("source")
        or metadata.get("document_name")
        or metadata.get("filename")
        or document[:60].strip()
        or f"Source {index + 1}"
    )


def _source_url(metadata: dict) -> str:
    return (
        metadata.get("url")
        or metadata.get("source_url")
        or metadata.get("link")
        or ""
    )


def retrieve_context(query: str, topic: str = "") -> RetrievalResult:
    try:
        collection = get_collection(create=False)
        results = collection.get(include=["documents", "metadatas"])
        all_documents = results.get("documents", []) or []
        all_metadatas = results.get("metadatas", []) or []

        ranked_items = []
        for index, document in enumerate(all_documents):
            metadata = all_metadatas[index] if index < len(all_metadatas) and all_metadatas[index] else {}
            metadata_topic = metadata.get("topic", "")
            if topic and metadata_topic and metadata_topic != topic:
                continue

            score = _relevance_score(query, document, metadata)
            if score <= 0:
                continue
            ranked_items.append((score, document, metadata))

        if topic and not ranked_items:
            for index, document in enumerate(all_documents):
                metadata = all_metadatas[index] if index < len(all_metadatas) and all_metadatas[index] else {}
                score = _relevance_score(query, document, metadata)
                if score <= 0:
                    continue
                ranked_items.append((score, document, metadata))

        if not ranked_items:
            return {"context": [], "sources": []}

        ranked_items.sort(key=lambda item: item[0], reverse=True)
        top_score = ranked_items[0][0]
        min_score = max(2, math.ceil(top_score * 0.6))
        ranked_items = [item for item in ranked_items if item[0] >= min_score]
        ranked_items = ranked_items[:5]

        source_scores: dict[tuple[str, str], int] = {}
        source_coverage: dict[tuple[str, str], int] = {}
        for score, _, metadata in ranked_items:
            source_key = (_source_title(metadata, "", 0), _source_url(metadata))
            source_scores[source_key] = max(source_scores.get(source_key, 0), score)
        for _, document, metadata in ranked_items:
            source_key = (_source_title(metadata, "", 0), _source_url(metadata))
            coverage = _coverage_count(query, document, metadata)
            source_coverage[source_key] = max(source_coverage.get(source_key, 0), coverage)

        if not source_scores:
            return {"context": [], "sources": []}

        top_source_score = max(source_scores.values())
        min_source_score = max(2, math.ceil(top_source_score * 0.75))
        query_token_count = len(set(_tokenize(query)))
        min_source_coverage = 1 if query_token_count <= 1 else math.ceil(query_token_count * 0.75)
        filtered_items = []
        for score, document, metadata in ranked_items:
            source_key = (_source_title(metadata, "", 0), _source_url(metadata))
            if (
                source_scores.get(source_key, 0) >= min_source_score
                and source_coverage.get(source_key, 0) >= min_source_coverage
            ):
                filtered_items.append((score, document, metadata))

        if not filtered_items:
            return {"context": [], "sources": []}

        ranked_items = filtered_items[:3]
        context = [document for _, document, _ in ranked_items]
        metadata_items = [metadata for _, _, metadata in ranked_items]

        sources: list[RetrievedSource] = []

        for index, document in enumerate(context):
            metadata = metadata_items[index] if index < len(metadata_items) and metadata_items[index] else {}
            title = _source_title(metadata, document, index)
            url = _source_url(metadata)

            if not any(source["title"] == title and source["url"] == url for source in sources):
                sources.append({"title": title, "url": url})

        return {"context": context, "sources": sources}
    except Exception as e:
        logger.warning(f"ChromaDB not available, returning empty context: {e}")
        return {"context": [], "sources": []}
