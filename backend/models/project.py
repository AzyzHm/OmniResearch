from datetime import datetime
from pydantic import BaseModel, field_validator

class ProjectCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Project name must be 100 characters or fewer.")
        return v


class ProjectUpdate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Project name must be 100 characters or fewer.")
        return v


class ProjectOut(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: datetime
    updated_at: datetime