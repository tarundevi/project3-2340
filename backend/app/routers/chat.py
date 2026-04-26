import time

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.auth import get_current_user
from app.services.persistence import PersistenceError, append_chat_exchange, ensure_conversation
from app.services.retriever import retrieve_context
from app.services.llm import generate_response
from app.services.usage_logger import log_query

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    start = time.monotonic()
    success = True
    sources = []
    conversation_id = request.conversation_id
    try:
        conversation = ensure_conversation(
            current_user["id"],
            conversation_id=request.conversation_id,
            topic=request.topic,
            first_message=request.message,
        )
        conversation_id = conversation["id"]
        retrieval = retrieve_context(request.message, request.topic)
        response_text = generate_response(request.message, retrieval["context"], request.topic)
        sources = retrieval["sources"]
        append_chat_exchange(
            current_user["id"],
            conversation_id,
            user_message=request.message,
            assistant_message=response_text,
            topic=request.topic,
            sources=sources,
        )
    except PersistenceError as exc:
        success = False
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        success = False
        raise
    finally:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log_query(
            query=f"[{current_user['email']}] {request.message}",
            topic=request.topic,
            response_time_ms=elapsed_ms,
            success=success,
        )

    return ChatResponse(response=response_text, sources=sources, conversation_id=conversation_id)
