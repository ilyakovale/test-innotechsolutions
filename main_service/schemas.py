from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MessageIn(BaseModel):
    text: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    username: str | None
    is_authenticated: bool
    created_at: datetime