import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.models.user import User
from app.schemas.gps import (
    GpsBatchIn,
    GpsBatchResult,
    GpsPositionOut,
    ShiftEndRequest,
    ShiftOut,
    ShiftStartRequest,
)
from app.services.gps_service import GpsService
from app.services.shift_service import ShiftService

shifts_router = APIRouter(prefix="/shifts", tags=["shifts"])
tracking_router = APIRouter(prefix="/tracking", tags=["tracking"])


@shifts_router.post("/start", response_model=ShiftOut, status_code=201)
def start_shift(
    payload: ShiftStartRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ShiftOut:
    return ShiftService(db).start_shift(payload, current_user)


@shifts_router.post("/{shift_id}/end", response_model=ShiftOut)
def end_shift(
    shift_id: uuid.UUID,
    payload: ShiftEndRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShiftOut:
    return ShiftService(db).end_shift(shift_id, payload, current_user)


@shifts_router.get("/{shift_id}/positions", response_model=list[GpsPositionOut])
def get_shift_positions(
    shift_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[GpsPositionOut]:
    return GpsService(db).get_history(shift_id)


@tracking_router.post("/location", response_model=GpsBatchResult)
def send_location_batch(
    payload: GpsBatchIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> GpsBatchResult:
    # Generoso pero acotado: protege contra un dispositivo comprometido/con bug
    # que intente floodear el endpoint, sin interferir con el uso normal (un
    # lote cada ~15s según docs/gps.md, este límite permite ráfagas razonables).
    check_rate_limit(f"ratelimit:gps:{current_user.id}", max_attempts=60, window_seconds=60)
    return GpsService(db).ingest_batch(payload, current_user)


@tracking_router.get("/live/{driver_id}")
def get_live_position(
    driver_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict:
    position = GpsService(db).get_live_position(driver_id)
    return position or {"status": "sin posición reciente"}
