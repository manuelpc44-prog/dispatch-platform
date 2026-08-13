import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceTokenRegister(BaseModel):
    token: str = Field(..., max_length=500)
    platform: str = Field(default="android", max_length=20)


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tipo: str
    titulo: str
    cuerpo: str | None
    leido: bool
    created_at: datetime
