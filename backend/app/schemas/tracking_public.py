import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ShipmentStatus


class TrackingTimelineEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    estado: ShipmentStatus
    created_at: datetime


class TrackingLivePosition(BaseModel):
    latitude: float
    longitude: float
    recorded_at: str


class TrackingPublicOut(BaseModel):
    """Vista pública y acotada de un despacho — nunca expone IDs internos,
    otros despachos, ni datos de otros clientes (ver docs/rbac.md regla 4)."""

    numero: str
    estado: ShipmentStatus
    destino_comuna: str
    destino_ciudad: str
    fecha_programada: date
    cliente_nombre: str
    timeline: list[TrackingTimelineEntry]
    live_position: TrackingLivePosition | None = None
