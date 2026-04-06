from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    topic: str = ""


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []
