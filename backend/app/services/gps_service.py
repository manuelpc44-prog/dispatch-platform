import json
import uuid

import redis
from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DomainError, Forbidden
from app.models.fleet import Driver
from app.models.gps import GpsPosition
from app.models.route import Route
from app.models.user import User
from app.repositories.gps_repository import GpsRepository, ShiftRepository
from app.schemas.gps import GpsBatchIn, GpsBatchResult, GpsPositionOut

LIVE_POSITION_TTL_SECONDS = 120


class NoActiveShift(DomainError):
    def __init__(self):
        super().__init__(
            "NO_ACTIVE_SHIFT",
            "El chofer no tiene una jornada activa — inicia jornada antes de enviar GPS",
            status.HTTP_409_CONFLICT,
        )


def _get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url)


class GpsService:
    def __init__(self, db: Session):
        self.db = db
        self.gps_repo = GpsRepository(db)
        self.shift_repo = ShiftRepository(db)

    def _get_driver(self, current_user: User) -> Driver:
        if "CHOFER" not in {r.name for r in current_user.roles}:
            raise Forbidden("Solo un chofer puede enviar posiciones GPS")
        driver = self.db.query(Driver).filter(Driver.user_id == current_user.id).first()
        if driver is None:
            raise Forbidden("El usuario actual no tiene un perfil de chofer asociado")
        return driver

    def ingest_batch(self, payload: GpsBatchIn, current_user: User) -> GpsBatchResult:
        driver = self._get_driver(current_user)
        shift = self.shift_repo.get_active_for_driver(driver.id)
        if shift is None:
            raise NoActiveShift()

        rows = [
            {
                "id": uuid.uuid4(),
                "client_uuid": p.client_uuid,
                "driver_shift_id": shift.id,
                "vehicle_id": shift.vehicle_id,
                "route_stop_id": None,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "accuracy": p.accuracy,
                "speed": p.speed,
                "heading": p.heading,
                "battery_level": p.battery_level,
                "network_status": p.network_status,
                "recorded_at": p.recorded_at,
            }
            for p in payload.positions
        ]
        inserted = self.gps_repo.bulk_insert(rows)
        self.db.commit()

        latest = max(payload.positions, key=lambda p: p.recorded_at)
        self._publish_live_position(driver, shift, latest)

        return GpsBatchResult(
            received=len(payload.positions), inserted=inserted, duplicates=len(payload.positions) - inserted
        )

    def _publish_live_position(self, driver: Driver, shift, latest) -> None:
        message = {
            "driver_id": str(driver.id),
            "driver_shift_id": str(shift.id),
            "vehicle_id": str(shift.vehicle_id),
            "latitude": latest.latitude,
            "longitude": latest.longitude,
            "speed": latest.speed,
            "heading": latest.heading,
            "recorded_at": latest.recorded_at.isoformat(),
        }
        r = _get_redis_client()
        try:
            r.set(f"live:driver:{driver.id}", json.dumps(message), ex=LIVE_POSITION_TTL_SECONDS)
            r.publish("gps:dispatcher:broadcast", json.dumps(message))

            routes = self.db.query(Route).filter(Route.driver_shift_id == shift.id).all()
            for route in routes:
                for stop in route.stops:
                    tracking_code = str(stop.shipment.tracking_code) if stop.shipment else None
                    if tracking_code:
                        r.publish(f"gps:tracking:{tracking_code}", json.dumps(message))
        finally:
            r.close()

    def get_live_position(self, driver_id: uuid.UUID) -> dict | None:
        r = _get_redis_client()
        try:
            raw = r.get(f"live:driver:{driver_id}")
            return json.loads(raw) if raw else None
        finally:
            r.close()

    def get_history(self, shift_id: uuid.UUID) -> list[GpsPositionOut]:
        positions = self.gps_repo.list_for_shift(shift_id)
        return [GpsPositionOut.model_validate(p) for p in positions]
