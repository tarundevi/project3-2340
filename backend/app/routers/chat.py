from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.retriever import retrieve_context
from app.services.llm import generate_response

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    context = retrieve_context(request.message)
    response_text = generate_response(request.message, context)
    return ChatResponse(response=response_text, sources=[])
