from datetime import datetime
from pydantic import BaseModel, Field

class UserOut(BaseModel):
    id: str
    username: str
    role: str
    is_approved: bool
    created_at: datetime
    daily_token_limit: int = 80_000


class UserListResponse(BaseModel):
    users: list[UserOut]
    total: int


class TokenLimitUpdate(BaseModel):
    daily_token_limit: int = Field(ge=0, le=100_000_000)