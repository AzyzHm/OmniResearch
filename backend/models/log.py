from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class LoginLogOut(BaseModel):
    id: str
    user_id: str
    username: str
    login_time: datetime
    ip_address: Optional[str] = None


class LoginLogListResponse(BaseModel):
    logs: list[LoginLogOut]
    total: int

class MessageResponse(BaseModel):
    message: str