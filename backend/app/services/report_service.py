import datetime
import math
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import DriverShiftStatus, ShipmentStatus
from app.models.fleet import Driver, Vehicle
from app.models.gps import GpsPosition
from app.models.route import DriverShift, Route, RouteStop
from app.models.shipment import Shipment, ShipmentStatusHistory
from app.models.user import User
from app.schemas.report import DashboardStats, RoutePositionOut, ShiftSummaryOut


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia entre dos puntos GPS en línea recta (no sigue calles). Ver
    docs/database.md — se evaluó PostGIS en Fase 2 como decisión abierta;
    para este alcance (reportes, no ruteo) alcanza con haversine en Python."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def _distance_for_shift(self, shift_id: uuid.UUID) -> float:
        positions = (
            self.db.query(GpsPosition.latitude, GpsPosition.longitude)
            .filter(GpsPosition.driver_shift_id == shift_id)
            .order_by(GpsPosition.recorded_at)
            .all()
        )
        total = 0.0
        for i in range(1, len(positions)):
            lat1, lon1 = float(positions[i - 1][0]), float(positions[i - 1][1])
            lat2, lon2 = float(positions[i][0]), float(positions[i][1])
            total += _haversine_km(lat1, lon1, lat2, lon2)
        return round(total, 2)

    def list_shifts(
        self, driver_id: uuid.UUID | None = None, fecha: datetime.date | None = None
    ) -> list[ShiftSummaryOut]:
        query = (
            self.db.query(DriverShift, Driver, User, Vehicle)
            .join(Driver, DriverShift.driver_id == Driver.id)
            .join(User, Driver.user_id == User.id)
            .join(Vehicle, DriverShift.vehicle_id == Vehicle.id)
        )
        if driver_id:
            query = query.filter(DriverShift.driver_id == driver_id)
        if fecha:
            query = query.filter(func.date(DriverShift.iniciada_at) == fecha)

        results = []
        for shift, driver, user, vehicle in query.order_by(DriverShift.iniciada_at.desc()).limit(100):
            duracion = None
            if shift.iniciada_at and shift.finalizada_at:
                duracion = round((shift.finalizada_at - shift.iniciada_at).total_seconds() / 60, 1)

            route_ids = [r.id for r in self.db.query(Route.id).filter(Route.driver_shift_id == shift.id).all()]
            despachos_count = 0
            entregados_count = 0
            if route_ids:
                stops = self.db.query(RouteStop.shipment_id).filter(RouteStop.route_id.in_(route_ids)).all()
                shipment_ids = [s[0] for s in stops]
                despachos_count = len(shipment_ids)
                if shipment_ids:
                    entregados_count = (
                        self.db.query(Shipment)
                        .filter(Shipment.id.in_(shipment_ids), Shipment.estado == ShipmentStatus.ENTREGADO)
                        .count()
                    )

            results.append(
                ShiftSummaryOut(
                    id=shift.id,
                    driver_id=driver.id,
                    driver_name=user.full_name,
                    vehicle_id=vehicle.id,
                    vehicle_plate=vehicle.plate,
                    estado=shift.estado.value,
                    iniciada_at=shift.iniciada_at,
                    finalizada_at=shift.finalizada_at,
                    distancia_km=self._distance_for_shift(shift.id),
                    duracion_minutos=duracion,
                    despachos_count=despachos_count,
                    entregados_count=entregados_count,
                )
            )
        return results

    def get_route_replay(self, shift_id: uuid.UUID) -> list[RoutePositionOut]:
        positions = (
            self.db.query(GpsPosition)
            .filter(GpsPosition.driver_shift_id == shift_id)
            .order_by(GpsPosition.recorded_at)
            .all()
        )
        return [
            RoutePositionOut(
                latitude=float(p.latitude),
                longitude=float(p.longitude),
                speed=float(p.speed) if p.speed is not None else None,
                recorded_at=p.recorded_at,
            )
            for p in positions
        ]

    def dashboard_stats(self) -> DashboardStats:
        today = datetime.date.today()

        shipments_today = self.db.query(Shipment).filter(Shipment.fecha_programada == today).all()
        counts = {status: 0 for status in ShipmentStatus}
        for s in shipments_today:
            counts[s.estado] += 1

        choferes_activos = (
            self.db.query(DriverShift)
            .filter(
                DriverShift.estado.in_(
                    [DriverShiftStatus.INICIADA, DriverShiftStatus.EN_RUTA, DriverShiftStatus.REGRESANDO]
                )
            )
            .distinct(DriverShift.driver_id)
            .count()
        )
        vehiculos_activos = (
            self.db.query(DriverShift)
            .filter(
                DriverShift.estado.in_(
                    [DriverShiftStatus.INICIADA, DriverShiftStatus.EN_RUTA, DriverShiftStatus.REGRESANDO]
                )
            )
            .distinct(DriverShift.vehicle_id)
            .count()
        )

        shifts_today = (
            self.db.query(DriverShift)
            .filter(func.date(DriverShift.iniciada_at) == today)
            .all()
        )
        distancia_total = round(sum(self._distance_for_shift(s.id) for s in shifts_today), 2)

        tiempo_promedio = self._avg_delivery_time_minutes(today)

        return DashboardStats(
            despachos_hoy=len(shipments_today),
            en_preparacion=counts[ShipmentStatus.PREPARANDO],
            asignados=counts[ShipmentStatus.ASIGNADO],
            en_ruta=counts[ShipmentStatus.EN_RUTA] + counts[ShipmentStatus.SALIDA_BODEGA],
            entregados=counts[ShipmentStatus.ENTREGADO],
            no_entregados=counts[ShipmentStatus.NO_ENTREGADO],
            incidencias=counts[ShipmentStatus.INCIDENCIA],
            choferes_activos=choferes_activos,
            vehiculos_activos=vehiculos_activos,
            distancia_recorrida_km_hoy=distancia_total,
            tiempo_promedio_entrega_minutos=tiempo_promedio,
        )

    def _avg_delivery_time_minutes(self, fecha: datetime.date) -> float | None:
        """Tiempo promedio entre SALIDA_BODEGA y ENTREGADO para despachos
        entregados hoy, calculado desde shipment_status_history."""
        shipments_entregados_hoy = (
            self.db.query(Shipment.id)
            .filter(Shipment.fecha_programada == fecha, Shipment.estado == ShipmentStatus.ENTREGADO)
            .all()
        )
        shipment_ids = [s[0] for s in shipments_entregados_hoy]
        if not shipment_ids:
            return None

        durations = []
        for shipment_id in shipment_ids:
            history = (
                self.db.query(ShipmentStatusHistory)
                .filter(ShipmentStatusHistory.shipment_id == shipment_id)
                .order_by(ShipmentStatusHistory.created_at)
                .all()
            )
            salida = next((h.created_at for h in history if h.estado_nuevo == ShipmentStatus.SALIDA_BODEGA), None)
            entregado = next((h.created_at for h in history if h.estado_nuevo == ShipmentStatus.ENTREGADO), None)
            if salida and entregado:
                durations.append((entregado - salida).total_seconds() / 60)

        if not durations:
            return None
        return round(sum(durations) / len(durations), 1)
