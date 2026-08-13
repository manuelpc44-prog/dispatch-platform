import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class VehicleBase(BaseModel):
    plate: str = Field(..., max_length=20)
    brand: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    capacity_kg: Decimal | None = None
    active: bool = True


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    plate: str | None = Field(None, max_length=20)
    brand: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    capacity_kg: Decimal | None = None
    active: bool | None = None


class VehicleOut(VehicleBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class DriverBase(BaseModel):
    license_number: str = Field(..., max_length=50)
    license_expiry: date | None = None
    active: bool = True


class DriverCreate(DriverBase):
    email: str = Field(..., max_length=255)
    full_name: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    phone: str | None = Field(None, max_length=50)


class DriverUpdate(BaseModel):
    license_number: str | None = Field(None, max_length=50)
    license_expiry: date | None = None
    active: bool | None = None


class DriverOut(DriverBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    email: str


class WarehouseBase(BaseModel):
    name: str = Field(..., max_length=255)
    address: str | None = Field(None, max_length=255)
    latitud: Decimal = Field(..., ge=-90, le=90)
    longitud: Decimal = Field(..., ge=-180, le=180)


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseOut(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
