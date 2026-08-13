import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DriverShiftStatus


class ShiftStartRequest(BaseModel):
    vehicle_id: uuid.UUID
    fecha: date | None = None  # por defecto hoy; explícito facilita las pruebas
    odometro_inicio: float | None = None


class ShiftEndRequest(BaseModel):
    odometro_fin: float | None = None


class ShiftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    estado: DriverShiftStatus
    iniciada_at: datetime | None
    finalizada_at: datetime | None


class GpsPositionIn(BaseModel):
    client_uuid: uuid.UUID
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: float | None = None
    speed: float | None = None
    heading: float | None = None
    battery_level: int | None = Field(None, ge=0, le=100)
    network_status: str | None = None
    recorded_at: datetime


class GpsBatchIn(BaseModel):
    positions: list[GpsPositionIn] = Field(..., min_length=1, max_length=500)


class GpsPositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    latitude: float
    longitude: float
    accuracy: float | None
    speed: float | None
    heading: float | None
    battery_level: int | None
    network_status: str | None
    recorded_at: datetime


class GpsBatchResult(BaseModel):
    received: int
    inserted: int
    duplicates: int
