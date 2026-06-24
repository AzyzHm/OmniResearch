from datetime import datetime
from pydantic import BaseModel, field_validator

class ChatCreate(BaseModel):
    name: str = "New Chat"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        return v.strip() or "New Chat"


class ChatUpdate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Chat name cannot be empty.")
        return v


class ChatOut(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime

class HistoryEntry(BaseModel):
    role: str       # "user" or "assistant"
    content: str


class ChatMessageRequest(BaseModel):
    message: str
    history: list[HistoryEntry] = []

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty.")
        return v


class ChatMessageResponse(BaseModel):
    response: str