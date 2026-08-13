import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.route import RouteCreate, RouteOut, RouteStopsReorderRequest
from app.services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteOut])
def list_routes(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[RouteOut]:
    return RouteService(db).list_routes(skip=skip, limit=limit)


@router.post("", response_model=RouteOut, status_code=201)
def create_route(
    payload: RouteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> RouteOut:
    return RouteService(db).create_route(payload, current_user)


@router.get("/{route_id}", response_model=RouteOut)
def get_route(
    route_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> RouteOut:
    return RouteService(db).get_route(route_id)


@router.patch("/{route_id}/stops/reorder", response_model=RouteOut)
def reorder_stops(
    route_id: uuid.UUID,
    payload: RouteStopsReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteOut:
    return RouteService(db).reorder_stops(route_id, payload, current_user)
