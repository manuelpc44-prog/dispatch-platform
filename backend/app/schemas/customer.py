import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class CustomerAddressBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    calle: str = Field(..., max_length=255)
    numero: str | None = Field(None, max_length=20)
    comuna: str = Field(..., max_length=100)
    ciudad: str = Field(..., max_length=100)
    region: str = Field(..., max_length=100)
    codigo_postal: str | None = Field(None, max_length=20)
    latitud: Decimal | None = Field(None, ge=-90, le=90)
    longitud: Decimal | None = Field(None, ge=-180, le=180)
    contacto: str | None = Field(None, max_length=255)
    telefono: str | None = Field(None, max_length=50)
    observaciones: str | None = Field(None, max_length=500)
    es_principal: bool = False
    activa: bool = True


class CustomerAddressCreate(CustomerAddressBase):
    pass


class CustomerAddressUpdate(BaseModel):
    nombre: str | None = Field(None, max_length=255)
    calle: str | None = Field(None, max_length=255)
    numero: str | None = Field(None, max_length=20)
    comuna: str | None = Field(None, max_length=100)
    ciudad: str | None = Field(None, max_length=100)
    region: str | None = Field(None, max_length=100)
    codigo_postal: str | None = Field(None, max_length=20)
    latitud: Decimal | None = Field(None, ge=-90, le=90)
    longitud: Decimal | None = Field(None, ge=-180, le=180)
    contacto: str | None = Field(None, max_length=255)
    telefono: str | None = Field(None, max_length=50)
    observaciones: str | None = Field(None, max_length=500)
    es_principal: bool | None = None
    activa: bool | None = None


class CustomerAddressOut(CustomerAddressBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    customer_id: uuid.UUID


class CustomerBase(BaseModel):
    business_name: str = Field(..., max_length=255)
    tax_id: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=50)
    email: EmailStr | None = None


class CustomerCreate(CustomerBase):
    seller_id: uuid.UUID | None = None
    address: CustomerAddressCreate | None = None


class CustomerUpdate(BaseModel):
    business_name: str | None = Field(None, max_length=255)
    tax_id: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    seller_id: uuid.UUID | None = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    seller_id: uuid.UUID | None = None


class CustomerWithAddressesOut(CustomerOut):
    addresses: list[CustomerAddressOut] = []
