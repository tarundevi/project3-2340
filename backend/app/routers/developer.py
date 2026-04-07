import time

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.ingestion import (
    IngestionError,
    clear_collection,
    delete_document,
    get_collection_overview,
    ingest_text_document,
    ingest_uploaded_file,
    ingest_url_document,
    is_duplicate_title,
    preprocess_text,
    reload_collection,
)
from app.services.llm import generate_response
from app.services.retriever import retrieve_context

router = APIRouter(prefix="/api/developer")


class TextIngestRequest(BaseModel):
    title: str
    content: str
    topic: str = ""
    url: str = ""


class UrlIngestRequest(BaseModel):
    url: str
    topic: str = ""


class DeleteDocumentRequest(BaseModel):
    title: str
    url: str = ""
    topic: str = ""


class EvalCase(BaseModel):
    question: str
    expected_keywords: str
    topic: str = ""


class EvalRequest(BaseModel):
    cases: list[EvalCase]


@router.get("/collection")
def collection_overview():
    return get_collection_overview()


@router.post("/preprocess")
def preprocess_preview(request: TextIngestRequest):
    result = preprocess_text(request.content)
    title = " ".join(request.title.split()).strip() or "Untitled Document"
    duplicate = is_duplicate_title(title)
    return {
        "original_word_count": result["original_word_count"],
        "cleaned_word_count": result["cleaned_word_count"],
        "words_removed": result["words_removed"],
        "preview": result["cleaned"][:300],
        "duplicate_warning": duplicate,
    }


@router.post("/collection/clear")
def clear_knowledge_base():
    return {
        "message": "Knowledge base cleared.",
        "collection": clear_collection(),
    }


@router.post("/collection/reload")
def reload_knowledge_base():
    return {
        "message": "Knowledge base embeddings reloaded from existing documents.",
        "collection": reload_collection(),
    }


@router.post("/ingest/text")
def ingest_text(request: TextIngestRequest):
    try:
        result = ingest_text_document(
            content=request.content,
            title=request.title,
            topic=request.topic,
            url=request.url,
        )
    except IngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    duplicate_msg = " Warning: duplicate title already exists." if result.get("duplicate_warning") else ""
    return {
        "message": f"Added {result['chunk_count']} chunk(s) from {result['title']}. Preprocessed: {result['original_word_count']} → {result['cleaned_word_count']} words.{duplicate_msg}",
        "document": result,
        "collection": get_collection_overview(),
    }


@router.post("/ingest/url")
def ingest_url(request: UrlIngestRequest):
    try:
        result = ingest_url_document(url=request.url, topic=request.topic)
    except IngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": f"Imported {result['title']} with {result['chunk_count']} chunk(s).",
        "document": result,
        "collection": get_collection_overview(),
    }


@router.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...), topic: str = Form(default="")):
    try:
        result = ingest_uploaded_file(
            filename=file.filename or "",
            content=await file.read(),
            topic=topic,
        )
    except IngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": f"Uploaded {result['title']} with {result['chunk_count']} chunk(s).",
        "document": result,
        "collection": get_collection_overview(),
    }


@router.post("/evaluate")
def evaluate_accuracy(request: EvalRequest):
    if not request.cases:
        raise HTTPException(status_code=400, detail="At least one test case is required.")

    results = []
    passed = 0

    for case in request.cases:
        if not case.question.strip():
            raise HTTPException(status_code=400, detail="Each test case must have a non-empty question.")
        if not case.expected_keywords.strip():
            raise HTTPException(status_code=400, detail="Each test case must have expected keywords.")

        start = time.monotonic()
        try:
            retrieval = retrieve_context(case.question, case.topic)
            actual_response = generate_response(case.question, retrieval["context"], case.topic)
            elapsed_ms = int((time.monotonic() - start) * 1000)

            keywords = [kw.strip().lower() for kw in case.expected_keywords.split(",") if kw.strip()]
            response_lower = actual_response.lower()
            matched = [kw for kw in keywords if kw in response_lower]
            missing = [kw for kw in keywords if kw not in response_lower]
            case_passed = len(missing) == 0

            if case_passed:
                passed += 1

            results.append({
                "question": case.question,
                "topic": case.topic,
                "expected_keywords": case.expected_keywords,
                "actual_response": actual_response,
                "matched_keywords": matched,
                "missing_keywords": missing,
                "passed": case_passed,
                "response_time_ms": elapsed_ms,
            })
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            results.append({
                "question": case.question,
                "topic": case.topic,
                "expected_keywords": case.expected_keywords,
                "actual_response": "",
                "matched_keywords": [],
                "missing_keywords": [kw.strip().lower() for kw in case.expected_keywords.split(",") if kw.strip()],
                "passed": False,
                "response_time_ms": elapsed_ms,
                "error": str(exc),
            })

    total = len(results)
    accuracy = round((passed / total) * 100, 1) if total > 0 else 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy_percent": accuracy,
        "results": results,
    }


@router.delete("/document")
def delete_document_endpoint(request: DeleteDocumentRequest):
    try:
        deleted_count = delete_document(
            title=request.title,
            url=request.url,
            topic=request.topic,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found in collection.")

    return {
        "message": f"Removed '{request.title}' ({deleted_count} chunk(s) deleted).",
        "collection": get_collection_overview(),
    }
