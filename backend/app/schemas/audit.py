import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID | None
    ip: str | None
    accion: str
    modulo: str
    registro_id: str | None
    valor_anterior: dict | None
    valor_nuevo: dict | None
    created_at: datetime
