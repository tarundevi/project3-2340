import time

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.retriever import retrieve_context
from app.services.llm import generate_response
from app.services.usage_logger import log_query

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    start = time.monotonic()
    success = True
    try:
        context = retrieve_context(request.message, request.topic)
        response_text = generate_response(request.message, context, request.topic)
    except Exception:
        success = False
        raise
    finally:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log_query(
            query=request.message,
            topic=request.topic,
            response_time_ms=elapsed_ms,
            success=success,
        )

    return ChatResponse(response=response_text, sources=[])
