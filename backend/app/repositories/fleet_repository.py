import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.fleet import Driver, Vehicle, Warehouse


class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, skip: int = 0, limit: int = 50) -> list[Vehicle]:
        return self.db.query(Vehicle).order_by(Vehicle.plate).offset(skip).limit(limit).all()

    def get(self, vehicle_id: uuid.UUID) -> Vehicle | None:
        return self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    def get_by_plate(self, plate: str) -> Vehicle | None:
        return self.db.query(Vehicle).filter(Vehicle.plate == plate).first()

    def create(self, vehicle: Vehicle) -> Vehicle:
        self.db.add(vehicle)
        self.db.flush()
        return vehicle

    def update(self, vehicle: Vehicle, **fields) -> Vehicle:
        for key, value in fields.items():
            if value is not None:
                setattr(vehicle, key, value)
        self.db.flush()
        return vehicle


class DriverRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, skip: int = 0, limit: int = 50) -> list[Driver]:
        return (
            self.db.query(Driver)
            .options(joinedload(Driver.user))
            .order_by(Driver.license_number)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get(self, driver_id: uuid.UUID) -> Driver | None:
        return (
            self.db.query(Driver)
            .options(joinedload(Driver.user))
            .filter(Driver.id == driver_id)
            .first()
        )

    def get_by_user_id(self, user_id: uuid.UUID) -> Driver | None:
        return self.db.query(Driver).filter(Driver.user_id == user_id).first()

    def create(self, driver: Driver) -> Driver:
        self.db.add(driver)
        self.db.flush()
        return driver

    def update(self, driver: Driver, **fields) -> Driver:
        for key, value in fields.items():
            if value is not None:
                setattr(driver, key, value)
        self.db.flush()
        return driver


class WarehouseRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Warehouse]:
        return self.db.query(Warehouse).order_by(Warehouse.name).all()

    def get(self, warehouse_id: uuid.UUID) -> Warehouse | None:
        return self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()

    def create(self, warehouse: Warehouse) -> Warehouse:
        self.db.add(warehouse)
        self.db.flush()
        return warehouse
