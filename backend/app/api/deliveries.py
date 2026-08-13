import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import DomainError
from app.db.session import get_db
from app.models.user import User
from app.schemas.delivery import (
    MOTIVOS_NO_ENTREGA,
    DeliveryCreate,
    DeliveryOut,
    EvidenceUploadOut,
    IncidentCreate,
    IncidentOut,
)
from app.services.delivery_service import DeliveryService, IncidentService

router = APIRouter(prefix="/deliveries", tags=["deliveries"])
incidents_router = APIRouter(prefix="/incidents", tags=["incidents"])

UPLOAD_DIR = Path("/tmp/dispatch-uploads/evidence")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB


class InvalidUpload(DomainError):
    def __init__(self, message: str):
        super().__init__("INVALID_UPLOAD", message, status.HTTP_400_BAD_REQUEST)


@router.get("/motivos-no-entrega", response_model=list[str])
def list_motivos() -> list[str]:
    return MOTIVOS_NO_ENTREGA


@router.post("/evidence", response_model=EvidenceUploadOut, status_code=201)
async def upload_evidence(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
) -> EvidenceUploadOut:
    """Almacenamiento local en disco para desarrollo. En producción esto debe
    apuntar a un bucket de object storage (S3, GCS, etc.) — ver docs/deployment.md
    (a completar en Fase 18); se deja como punto único de cambio."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidUpload(f"Extensión no permitida: {ext or '(sin extensión)'}")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise InvalidUpload("El archivo supera el tamaño máximo permitido (8 MB)")

    filename = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(contents)

    return EvidenceUploadOut(url=f"/media/evidence/{filename}")


@router.post("", response_model=DeliveryOut, status_code=201)
def create_delivery(
    payload: DeliveryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DeliveryOut:
    return DeliveryService(db).create_delivery(payload, current_user)


@router.get("/by-shipment/{shipment_id}", response_model=DeliveryOut | None)
def get_delivery_by_shipment(
    shipment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DeliveryOut | None:
    return DeliveryService(db).get_by_shipment(shipment_id, current_user)


@incidents_router.post("", response_model=IncidentOut, status_code=201)
def create_incident(
    payload: IncidentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> IncidentOut:
    return IncidentService(db).create_incident(payload, current_user)


@incidents_router.get("/by-shipment/{shipment_id}", response_model=list[IncidentOut])
def list_incidents(
    shipment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[IncidentOut]:
    return IncidentService(db).list_for_shipment(shipment_id, current_user)
