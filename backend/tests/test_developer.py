from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import ingestion

client = TestClient(app)


def test_ingest_text_adds_document(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.config.settings.chroma_persist_dir", str(tmp_path / "chromadb"))

    response = client.post(
        "/api/developer/ingest/text",
        json={
            "title": "Protein Basics",
            "content": "Protein supports muscle repair and growth.",
            "topic": "macronutrients",
            "url": "https://example.com/protein",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["title"] == "Protein Basics"
    assert data["collection"]["exists"] is True
    assert data["collection"]["chunk_count"] >= 1


def test_ingest_url_adds_document(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.config.settings.chroma_persist_dir", str(tmp_path / "chromadb"))

    def fake_fetch(url: str):
        return {
            "title": "Hydration Guide",
            "content": "Water needs vary by person and activity level.",
            "url": url,
        }

    monkeypatch.setattr(ingestion, "fetch_url_document", fake_fetch)

    response = client.post(
        "/api/developer/ingest/url",
        json={
            "url": "https://example.com/hydration",
            "topic": "hydration",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["title"] == "Hydration Guide"
    assert data["collection"]["exists"] is True
    assert data["collection"]["documents"][0]["url"] == "https://example.com/hydration"


def test_collection_overview_empty(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.config.settings.chroma_persist_dir", str(tmp_path / "chromadb"))

    response = client.get("/api/developer/collection")

    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False
    assert data["chunk_count"] == 0


def test_ingest_file_adds_document(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.config.settings.chroma_persist_dir", str(tmp_path / "chromadb"))

    response = client.post(
        "/api/developer/ingest/file",
        data={"topic": "food_safety"},
        files={"file": ("food_safety.txt", b"Keep cold foods refrigerated below 40F.", "text/plain")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["title"] == "food safety"
    assert data["collection"]["exists"] is True


def test_ingest_file_rejects_unsupported_extension(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.config.settings.chroma_persist_dir", str(tmp_path / "chromadb"))

    response = client.post(
        "/api/developer/ingest/file",
        data={"topic": "food_safety"},
        files={"file": ("notes.exe", b"not-a-supported-file", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_ingest_file_rejects_invalid_pdf(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.config.settings.chroma_persist_dir", str(tmp_path / "chromadb"))

    response = client.post(
        "/api/developer/ingest/file",
        data={"topic": "food_safety"},
        files={"file": ("notes.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert response.status_code == 400
    assert "PDF could not be opened." in response.json()["detail"]


def test_ingest_pdf_file_adds_document(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.config.settings.chroma_persist_dir", str(tmp_path / "chromadb"))

    class FakePage:
        def extract_text(self):
            return "Vitamin D supports calcium absorption."

    class FakeReader:
        def __init__(self, _):
            self.pages = [FakePage()]

    monkeypatch.setattr("app.services.ingestion.PdfReader", FakeReader)

    response = client.post(
        "/api/developer/ingest/file",
        data={"topic": "vitamins_minerals"},
        files={"file": ("vitamin_d.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["title"] == "vitamin d"
    assert data["collection"]["exists"] is True
