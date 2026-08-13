import datetime
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import DashboardStats, RoutePositionOut, ShiftSummaryOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
_reports_access = require_role("ADMINISTRADOR", "DESPACHADOR")


@router.get("/shifts", response_model=list[ShiftSummaryOut])
def list_shifts(
    driver_id: uuid.UUID | None = None,
    fecha: datetime.date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(_reports_access),
) -> list[ShiftSummaryOut]:
    return ReportService(db).list_shifts(driver_id=driver_id, fecha=fecha)


@router.get("/shifts/{shift_id}/replay", response_model=list[RoutePositionOut])
def get_route_replay(
    shift_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(_reports_access)
) -> list[RoutePositionOut]:
    return ReportService(db).get_route_replay(shift_id)


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db), current_user: User = Depends(_reports_access)
) -> DashboardStats:
    return ReportService(db).dashboard_stats()
