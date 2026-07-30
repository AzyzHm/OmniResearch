from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

EXT_TO_SOURCE_TYPE = {
    ".pdf": "pdf",
    ".txt": "txt",
}
ALLOWED_UPLOAD_EXTENSIONS = tuple(EXT_TO_SOURCE_TYPE)


class CollectionCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Collection name cannot be empty.")
        return v


class CollectionOut(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime


class CollectionItemOut(BaseModel):
    id: str
    collection_id: str
    name: str
    source_type: str
    is_active: bool
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime


class CollectionItemUpdate(BaseModel):
    is_active: bool


class BulkItemUpdate(BaseModel):
    item_id: str
    is_active: bool


class BulkItemsUpdateRequest(BaseModel):
    updates: list[BulkItemUpdate]

    @field_validator("updates")
    @classmethod
    def updates_not_empty(cls, v: list[BulkItemUpdate]) -> list[BulkItemUpdate]:
        if not v:
            raise ValueError("No changes to apply.")
        return v