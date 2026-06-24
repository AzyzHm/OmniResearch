from datetime import datetime
from pydantic import BaseModel, field_validator

COLLECTION_TYPES = ("documents", "urls", "text")

class CollectionCreate(BaseModel):
    name: str
    type: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Collection name cannot be empty.")
        return v

    @field_validator("type")
    @classmethod
    def type_valid(cls, v: str) -> str:
        if v not in COLLECTION_TYPES:
            raise ValueError(f"type must be one of: {', '.join(COLLECTION_TYPES)}")
        return v


class CollectionOut(BaseModel):
    id: str
    project_id: str
    name: str
    type: str
    created_at: datetime