import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DeliveryResult, EvidenceType

MOTIVOS_NO_ENTREGA = [
    "Cliente ausente",
    "Dirección incorrecta",
    "Cliente rechazó",
    "Problema de acceso",
    "Problema vehículo",
    "Otro",
]


class DeliveryEvidenceIn(BaseModel):
    tipo: EvidenceType
    url: str = Field(..., max_length=500)


class DeliveryCreate(BaseModel):
    shipment_id: uuid.UUID
    resultado: DeliveryResult
    receptor_nombre: str | None = None
    motivo_fallo: str | None = None
    observacion: str | None = None
    gps_lat: float | None = None
    gps_lng: float | None = None
    evidence: list[DeliveryEvidenceIn] = []


class DeliveryEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tipo: EvidenceType
    url: str


class DeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    shipment_id: uuid.UUID
    receptor_nombre: str | None
    resultado: DeliveryResult
    motivo_fallo: str | None
    observacion: str | None
    evidence: list[DeliveryEvidenceOut] = []


class IncidentCreate(BaseModel):
    shipment_id: uuid.UUID
    tipo: str = Field(..., max_length=50)
    descripcion: str | None = None
    gps_lat: float | None = None
    gps_lng: float | None = None


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    shipment_id: uuid.UUID
    driver_id: uuid.UUID | None
    tipo: str
    descripcion: str | None
    resuelto: bool
    created_at: datetime


class EvidenceUploadOut(BaseModel):
    url: str
