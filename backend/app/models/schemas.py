from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    topic: str = ""


class SourceItem(BaseModel):
    title: str
    url: str = ""


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceItem] = []


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
