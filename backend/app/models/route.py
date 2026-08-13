import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import DriverShiftStatus
from app.models.mixins import TimestampMixin
from app.models.shipment import Shipment

driver_shift_status_enum = PGEnum(DriverShiftStatus, name="driver_shift_status", create_type=True)


class DriverShift(TimestampMixin, Base):
    """Jornada de un chofer: ancla temporal que separa el GPS de una jornada de otra.
    Se crea cuando el chofer presiona 'Iniciar Jornada' en la app (Fase 11), no cuando
    el despachador asigna despachos (Fase 7) — ver Route.driver_id/vehicle_id."""

    __tablename__ = "driver_shifts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    estado: Mapped[DriverShiftStatus] = mapped_column(
        driver_shift_status_enum, default=DriverShiftStatus.INICIADA, nullable=False
    )
    odometro_inicio: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    odometro_fin: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    iniciada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalizada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    routes: Mapped[list["Route"]] = relationship(back_populates="driver_shift")


class Route(TimestampMixin, Base):
    """Una ruta es la asignación de N despachos a un chofer+vehículo para una fecha.
    Se crea en Fase 7 (asignación por el despachador) con driver_shift_id NULO;
    se vincula a una DriverShift real cuando el chofer inicia su jornada (Fase 11)."""

    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_shift_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("driver_shifts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(30), default="PLANIFICADA", nullable=False)

    driver_shift: Mapped["DriverShift | None"] = relationship(back_populates="routes")
    stops: Mapped[list["RouteStop"]] = relationship(
        back_populates="route", cascade="all, delete-orphan", order_by="RouteStop.orden"
    )


class RouteStop(TimestampMixin, Base):
    __tablename__ = "route_stops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), default="PENDIENTE", nullable=False)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ata: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    route: Mapped["Route"] = relationship(back_populates="stops")
    shipment: Mapped["Shipment"] = relationship()
