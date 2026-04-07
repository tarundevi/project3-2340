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
