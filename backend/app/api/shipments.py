import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentOut,
    ShipmentStatusHistoryOut,
    ShipmentTransitionRequest,
    ShipmentUpdate,
)
from app.schemas.tracking_public import TrackingPublicOut
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/shipments", tags=["shipments"])
public_router = APIRouter(prefix="/public", tags=["public-tracking"])


@public_router.get("/tracking/{tracking_code}", response_model=TrackingPublicOut)
def public_tracking(tracking_code: uuid.UUID, db: Session = Depends(get_db)) -> TrackingPublicOut:
    """Endpoint público — SIN autenticación. Protegido únicamente por que
    tracking_code es un UUID v4 no adivinable (ver docs/rbac.md regla 4 y
    sección 28 del prompt: /seguimiento/{tracking_code})."""
    return ShipmentService(db).get_public_tracking(tracking_code)


@router.get("", response_model=list[ShipmentOut])
def list_shipments(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ShipmentOut]:
    return ShipmentService(db).list_shipments(current_user, skip=skip, limit=limit)


@router.post("", response_model=ShipmentOut, status_code=201)
def create_shipment(
    payload: ShipmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ShipmentOut:
    return ShipmentService(db).create_shipment(payload, current_user)


@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment(
    shipment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ShipmentOut:
    return ShipmentService(db).get_shipment(shipment_id, current_user)


@router.patch("/{shipment_id}", response_model=ShipmentOut)
def update_shipment(
    shipment_id: uuid.UUID,
    payload: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentOut:
    return ShipmentService(db).update_shipment(shipment_id, payload, current_user)


@router.post("/{shipment_id}/status", response_model=ShipmentOut)
def transition_status(
    shipment_id: uuid.UUID,
    payload: ShipmentTransitionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentOut:
    client_ip = request.client.host if request.client else None
    return ShipmentService(db).transition(shipment_id, payload, current_user, ip=client_ip)


@router.get("/{shipment_id}/history", response_model=list[ShipmentStatusHistoryOut])
def get_history(
    shipment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ShipmentStatusHistoryOut]:
    return ShipmentService(db).get_history(shipment_id, current_user)
