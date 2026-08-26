from datetime import datetime

from pydantic import BaseModel


class LoginLogOut(BaseModel):
    id: str
    user_id: str
    username: str
    login_time: datetime
    ip_address: str | None = None


class LoginLogListResponse(BaseModel):
    logs: list[LoginLogOut]
    total: int


class MessageResponse(BaseModel):
    message: str
