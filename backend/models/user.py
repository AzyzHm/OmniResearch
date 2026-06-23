from datetime import datetime
from pydantic import BaseModel

class UserOut(BaseModel):
    id: str
    username: str
    role: str
    is_approved: bool
    created_at: datetime


class UserListResponse(BaseModel):
    users: list[UserOut]
    total: int