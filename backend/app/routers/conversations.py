from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import ConversationDetail, ConversationSummary, CreateConversationRequest
from app.services.auth import get_current_user
from app.services.persistence import PersistenceError, create_conversation, get_conversation, list_conversations

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
def list_user_conversations(current_user: dict = Depends(get_current_user)):
    return list_conversations(current_user["id"])


@router.post("", response_model=ConversationSummary)
def create_user_conversation(
    request: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
):
    return create_conversation(current_user["id"], title=request.title, topic=request.topic)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_user_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        return get_conversation(current_user["id"], conversation_id)
    except PersistenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
