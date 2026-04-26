from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    topic: str = ""
    conversation_id: str = ""


class SourceItem(BaseModel):
    title: str
    url: str = ""


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceItem] = []
    conversation_id: str = ""


class AuthCredentials(BaseModel):
    email: str
    password: str


class AuthUser(BaseModel):
    id: str
    email: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class MessageItem(BaseModel):
    role: str
    content: str
    topic: str = ""
    created_at: str
    sources: list[SourceItem] = []


class ConversationSummary(BaseModel):
    id: str
    title: str
    topic: str = ""
    created_at: str
    updated_at: str
    last_message_preview: str = ""


class ConversationDetail(BaseModel):
    conversation: ConversationSummary
    messages: list[MessageItem]


class CreateConversationRequest(BaseModel):
    title: str = ""
    topic: str = ""
