import uuid

from fastapi import status
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, Forbidden
from app.core.security import hash_password
from app.models.fleet import Driver, Vehicle, Warehouse
from app.models.user import Role, User
from app.models.enums import RoleName
from app.repositories.fleet_repository import DriverRepository, VehicleRepository, WarehouseRepository
from app.schemas.fleet import DriverCreate, DriverUpdate, VehicleCreate, VehicleUpdate, WarehouseCreate


class VehicleNotFound(DomainError):
    def __init__(self):
        super().__init__("VEHICLE_NOT_FOUND", "Vehículo no encontrado", status.HTTP_404_NOT_FOUND)


class DriverNotFound(DomainError):
    def __init__(self):
        super().__init__("DRIVER_NOT_FOUND", "Chofer no encontrado", status.HTTP_404_NOT_FOUND)


class DuplicatePlate(DomainError):
    def __init__(self):
        super().__init__("DUPLICATE_PLATE", "Ya existe un vehículo con esa patente", status.HTTP_409_CONFLICT)


class DuplicateEmail(DomainError):
    def __init__(self):
        super().__init__("DUPLICATE_EMAIL", "Ya existe un usuario con ese correo", status.HTTP_409_CONFLICT)


def _assert_admin(current_user: User) -> None:
    if "ADMINISTRADOR" not in {r.name for r in current_user.roles}:
        raise Forbidden("Solo ADMINISTRADOR puede crear/editar vehículos, choferes y bodegas")


class VehicleService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VehicleRepository(db)

    def list(self, skip: int = 0, limit: int = 50) -> list[Vehicle]:
        return self.repo.list(skip=skip, limit=limit)

    def get(self, vehicle_id: uuid.UUID) -> Vehicle:
        vehicle = self.repo.get(vehicle_id)
        if vehicle is None:
            raise VehicleNotFound()
        return vehicle

    def create(self, payload: VehicleCreate, current_user: User) -> Vehicle:
        _assert_admin(current_user)
        if self.repo.get_by_plate(payload.plate):
            raise DuplicatePlate()
        vehicle = Vehicle(**payload.model_dump())
        self.repo.create(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def update(self, vehicle_id: uuid.UUID, payload: VehicleUpdate, current_user: User) -> Vehicle:
        _assert_admin(current_user)
        vehicle = self.get(vehicle_id)
        if payload.plate and payload.plate != vehicle.plate and self.repo.get_by_plate(payload.plate):
            raise DuplicatePlate()
        self.repo.update(vehicle, **payload.model_dump(exclude_unset=True))
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle


class DriverService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DriverRepository(db)

    def list(self, skip: int = 0, limit: int = 50) -> list[Driver]:
        return self.repo.list(skip=skip, limit=limit)

    def get(self, driver_id: uuid.UUID) -> Driver:
        driver = self.repo.get(driver_id)
        if driver is None:
            raise DriverNotFound()
        return driver

    def create(self, payload: DriverCreate, current_user: User, ip: str | None = None) -> Driver:
        _assert_admin(current_user)

        existing_user = self.db.query(User).filter(User.email == payload.email).first()
        if existing_user:
            raise DuplicateEmail()

        chofer_role = self.db.query(Role).filter(Role.name == RoleName.CHOFER.value).first()

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            is_active=True,
        )
        user.roles.append(chofer_role)
        self.db.add(user)
        self.db.flush()

        driver = Driver(
            user_id=user.id,
            license_number=payload.license_number,
            license_expiry=payload.license_expiry,
            active=payload.active,
        )
        self.repo.create(driver)
        self.db.commit()
        self.db.refresh(driver)

        from app.services.audit_service import AuditService

        AuditService(self.db).log_action(
            user_id=current_user.id,
            ip=ip,
            accion="CREATE",
            modulo="drivers",
            registro_id=str(driver.id),
            valor_nuevo={"email": payload.email, "license_number": payload.license_number},
        )

        return driver

    def update(self, driver_id: uuid.UUID, payload: DriverUpdate, current_user: User) -> Driver:
        _assert_admin(current_user)
        driver = self.get(driver_id)
        self.repo.update(driver, **payload.model_dump(exclude_unset=True))
        self.db.commit()
        self.db.refresh(driver)
        return driver


class WarehouseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = WarehouseRepository(db)

    def list(self) -> list[Warehouse]:
        return self.repo.list()

    def create(self, payload: WarehouseCreate, current_user: User) -> Warehouse:
        _assert_admin(current_user)
        warehouse = Warehouse(**payload.model_dump())
        self.repo.create(warehouse)
        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse
