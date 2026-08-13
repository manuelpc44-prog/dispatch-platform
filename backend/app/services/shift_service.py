import datetime
import uuid

from fastapi import status
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, Forbidden
from app.models.enums import DriverShiftStatus
from app.models.fleet import Driver
from app.models.route import DriverShift
from app.models.user import User
from app.repositories.gps_repository import ShiftRepository
from app.schemas.gps import ShiftEndRequest, ShiftStartRequest


class DriverProfileNotFound(DomainError):
    def __init__(self):
        super().__init__(
            "DRIVER_PROFILE_NOT_FOUND",
            "El usuario actual no tiene un perfil de chofer asociado",
            status.HTTP_403_FORBIDDEN,
        )


class ShiftAlreadyActive(DomainError):
    def __init__(self):
        super().__init__(
            "SHIFT_ALREADY_ACTIVE", "Ya existe una jornada activa para este chofer", status.HTTP_409_CONFLICT
        )


class ShiftNotFound(DomainError):
    def __init__(self):
        super().__init__("SHIFT_NOT_FOUND", "Jornada no encontrada", status.HTTP_404_NOT_FOUND)


class ShiftNotOwned(DomainError):
    def __init__(self):
        super().__init__(
            "SHIFT_NOT_OWNED", "Esta jornada no pertenece al chofer autenticado", status.HTTP_403_FORBIDDEN
        )


def _get_driver_or_raise(db: Session, current_user: User) -> Driver:
    if "CHOFER" not in {r.name for r in current_user.roles}:
        raise Forbidden("Solo un usuario con rol CHOFER puede iniciar/finalizar jornadas")
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if driver is None:
        raise DriverProfileNotFound()
    return driver


class ShiftService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ShiftRepository(db)

    def start_shift(self, payload: ShiftStartRequest, current_user: User) -> DriverShift:
        driver = _get_driver_or_raise(self.db, current_user)

        if self.repo.get_active_for_driver(driver.id) is not None:
            raise ShiftAlreadyActive()

        fecha = payload.fecha or datetime.date.today()
        shift = DriverShift(
            driver_id=driver.id,
            vehicle_id=payload.vehicle_id,
            estado=DriverShiftStatus.INICIADA,
            odometro_inicio=payload.odometro_inicio,
            iniciada_at=datetime.datetime.now(datetime.timezone.utc),
        )
        self.repo.create(shift)

        # Vincular las rutas ya asignadas para este chofer+vehículo+fecha (Fase 7)
        routes = self.repo.find_assigned_routes(driver.id, payload.vehicle_id, fecha)
        for route in routes:
            route.driver_shift_id = shift.id
            route.estado = "EN_CURSO"

        self.db.commit()
        self.db.refresh(shift)
        return shift

    def end_shift(self, shift_id: uuid.UUID, payload: ShiftEndRequest, current_user: User) -> DriverShift:
        driver = _get_driver_or_raise(self.db, current_user)
        shift = self.repo.get(shift_id)
        if shift is None:
            raise ShiftNotFound()
        if shift.driver_id != driver.id:
            raise ShiftNotOwned()

        shift.estado = DriverShiftStatus.FINALIZADA
        shift.odometro_fin = payload.odometro_fin
        shift.finalizada_at = datetime.datetime.now(datetime.timezone.utc)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def get_active_shift_for_current_driver(self, current_user: User) -> DriverShift | None:
        driver = _get_driver_or_raise(self.db, current_user)
        return self.repo.get_active_for_driver(driver.id)
