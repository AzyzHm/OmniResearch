from datetime import datetime

from pydantic import BaseModel, field_validator

from models.chat import Source


class NoteCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Note name cannot be empty.")
        return v


class NoteUpdate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Note name cannot be empty.")
        return v


class NoteOut(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime


class NoteItemCreate(BaseModel):
    message_id: str


class NoteItemOut(BaseModel):
    id: str
    note_id: str
    message_id: str
    chat_id: str
    role: str
    content: str
    sources: list[Source] | None = None
    created_at: datetime