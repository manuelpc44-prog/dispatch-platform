import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ShipmentStatus


class ShipmentItemCreate(BaseModel):
    descripcion: str = Field(..., max_length=255)
    cantidad: float = 1
    unidad: str | None = Field(None, max_length=20)


class ShipmentItemOut(ShipmentItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class ShipmentCreate(BaseModel):
    customer_id: uuid.UUID
    address_id: uuid.UUID
    warehouse_id: uuid.UUID
    fecha_programada: date
    hora_programada: time | None = None
    prioridad: str = "NORMAL"
    observaciones: str | None = None
    items: list[ShipmentItemCreate] = []


class ShipmentUpdate(BaseModel):
    fecha_programada: date | None = None
    hora_programada: time | None = None
    prioridad: str | None = None
    observaciones: str | None = None


class ShipmentTransitionRequest(BaseModel):
    nuevo_estado: ShipmentStatus
    observacion: str | None = None
    gps_lat: float | None = None
    gps_lng: float | None = None


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    numero: str
    tracking_code: uuid.UUID
    customer_id: uuid.UUID
    address_id: uuid.UUID
    seller_id: uuid.UUID | None
    warehouse_id: uuid.UUID
    driver_id: uuid.UUID | None
    vehicle_id: uuid.UUID | None
    fecha_programada: date
    hora_programada: time | None
    prioridad: str
    estado: ShipmentStatus
    observaciones: str | None
    items: list[ShipmentItemOut] = []


class ShipmentStatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estado_anterior: ShipmentStatus | None
    estado_nuevo: ShipmentStatus
    user_id: uuid.UUID | None
    observacion: str | None
    created_at: datetime
