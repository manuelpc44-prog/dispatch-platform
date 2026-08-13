import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.fleet import Driver
from app.models.user import User
from app.schemas.fleet import (
    DriverCreate,
    DriverOut,
    DriverUpdate,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
    WarehouseCreate,
    WarehouseOut,
)
from app.services.fleet_service import DriverService, VehicleService, WarehouseService

vehicles_router = APIRouter(prefix="/vehicles", tags=["vehicles"])
drivers_router = APIRouter(prefix="/drivers", tags=["drivers"])
warehouses_router = APIRouter(prefix="/warehouses", tags=["warehouses"])


def _driver_to_out(driver: Driver) -> DriverOut:
    return DriverOut(
        id=driver.id,
        user_id=driver.user_id,
        license_number=driver.license_number,
        license_expiry=driver.license_expiry,
        active=driver.active,
        full_name=driver.user.full_name,
        email=driver.user.email,
    )


@vehicles_router.get("", response_model=list[VehicleOut])
def list_vehicles(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[VehicleOut]:
    return VehicleService(db).list(skip=skip, limit=limit)


@vehicles_router.post("", response_model=VehicleOut, status_code=201)
def create_vehicle(
    payload: VehicleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> VehicleOut:
    return VehicleService(db).create(payload, current_user)


@vehicles_router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(
    vehicle_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> VehicleOut:
    return VehicleService(db).get(vehicle_id)


@vehicles_router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: uuid.UUID,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VehicleOut:
    return VehicleService(db).update(vehicle_id, payload, current_user)


@drivers_router.get("", response_model=list[DriverOut])
def list_drivers(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[DriverOut]:
    drivers = DriverService(db).list(skip=skip, limit=limit)
    return [_driver_to_out(d) for d in drivers]


@drivers_router.post("", response_model=DriverOut, status_code=201)
def create_driver(
    payload: DriverCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverOut:
    client_ip = request.client.host if request.client else None
    driver = DriverService(db).create(payload, current_user, ip=client_ip)
    return _driver_to_out(driver)


@drivers_router.get("/{driver_id}", response_model=DriverOut)
def get_driver(
    driver_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DriverOut:
    driver = DriverService(db).get(driver_id)
    return _driver_to_out(driver)


@drivers_router.patch("/{driver_id}", response_model=DriverOut)
def update_driver(
    driver_id: uuid.UUID,
    payload: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverOut:
    driver = DriverService(db).update(driver_id, payload, current_user)
    return _driver_to_out(driver)


@warehouses_router.get("", response_model=list[WarehouseOut])
def list_warehouses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[WarehouseOut]:
    return WarehouseService(db).list()


@warehouses_router.post("", response_model=WarehouseOut, status_code=201)
def create_warehouse(
    payload: WarehouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> WarehouseOut:
    return WarehouseService(db).create(payload, current_user)
