from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.ingestion import (
    IngestionError,
    delete_document,
    get_collection_overview,
    ingest_text_document,
    ingest_uploaded_file,
    ingest_url_document,
)

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


@router.get("/collection")
def collection_overview():
    return get_collection_overview()


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

    return {
        "message": f"Added {result['chunk_count']} chunk(s) from {result['title']}.",
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
