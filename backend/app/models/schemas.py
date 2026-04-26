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
    role_key: str = ""


class AuthUser(BaseModel):
    id: str
    email: str
    role: str = "user"


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


class UserProfile(BaseModel):
    raw_text: str = ""
    summary: list[str] = []
    updated_at: str = ""


class ProfileRequest(BaseModel):
    raw_text: str


class IngredientCheckRequest(BaseModel):
    ingredient: str


class IngredientCheckResponse(BaseModel):
    response: str
    sources: list[SourceItem] = []
