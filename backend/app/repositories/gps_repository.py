import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.enums import DriverShiftStatus
from app.models.gps import GpsPosition
from app.models.route import DriverShift, Route


class ShiftRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_for_driver(self, driver_id: uuid.UUID) -> DriverShift | None:
        return (
            self.db.query(DriverShift)
            .filter(
                DriverShift.driver_id == driver_id,
                DriverShift.estado.in_([DriverShiftStatus.INICIADA, DriverShiftStatus.EN_RUTA, DriverShiftStatus.REGRESANDO]),
            )
            .first()
        )

    def get(self, shift_id: uuid.UUID) -> DriverShift | None:
        return self.db.query(DriverShift).filter(DriverShift.id == shift_id).first()

    def create(self, shift: DriverShift) -> DriverShift:
        self.db.add(shift)
        self.db.flush()
        return shift

    def find_assigned_routes(self, driver_id: uuid.UUID, vehicle_id: uuid.UUID, fecha) -> list[Route]:
        return (
            self.db.query(Route)
            .filter(
                Route.driver_id == driver_id,
                Route.vehicle_id == vehicle_id,
                Route.fecha == fecha,
                Route.estado == "ASIGNADA",
            )
            .all()
        )


class GpsRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_insert(self, rows: list[dict]) -> int:
        """Inserción idempotente por client_uuid (ver docs/gps.md sección 3).
        Devuelve la cantidad de filas efectivamente insertadas (no duplicadas).

        Nota: rowcount de executemany con ON CONFLICT DO NOTHING no es confiable en
        este driver (devuelve -1) — se usa RETURNING id y se cuenta lo devuelto."""
        if not rows:
            return 0
        stmt = pg_insert(GpsPosition).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["client_uuid"]).returning(GpsPosition.id)
        result = self.db.execute(stmt)
        inserted_count = len(result.fetchall())
        self.db.flush()
        return inserted_count

    def list_for_shift(self, driver_shift_id: uuid.UUID, skip: int = 0, limit: int = 500) -> list[GpsPosition]:
        return (
            self.db.query(GpsPosition)
            .filter(GpsPosition.driver_shift_id == driver_shift_id)
            .order_by(GpsPosition.recorded_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
