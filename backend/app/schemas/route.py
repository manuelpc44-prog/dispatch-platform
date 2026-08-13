import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class RouteCreate(BaseModel):
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    warehouse_id: uuid.UUID
    fecha: date
    shipment_ids: list[uuid.UUID] = Field(..., min_length=1)


class RouteStopReorderItem(BaseModel):
    stop_id: uuid.UUID
    orden: int


class RouteStopsReorderRequest(BaseModel):
    stops: list[RouteStopReorderItem] = Field(..., min_length=1)


class RouteStopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    shipment_id: uuid.UUID
    orden: int
    estado: str
    eta: datetime | None
    ata: datetime | None


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    driver_shift_id: uuid.UUID | None
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    warehouse_id: uuid.UUID
    fecha: date
    estado: str
    stops: list[RouteStopOut] = []
