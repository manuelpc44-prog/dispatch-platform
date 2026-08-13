import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, Time, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import ShipmentStatus
from app.models.mixins import TimestampMixin

shipment_status_enum = PGEnum(
    ShipmentStatus, name="shipment_status", create_type=True
)


class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    tracking_code: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    address_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_addresses.id", ondelete="RESTRICT"), nullable=False
    )
    seller_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )
    fecha_programada: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora_programada: Mapped[time | None] = mapped_column(Time, nullable=True)
    prioridad: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)
    estado: Mapped[ShipmentStatus] = mapped_column(
        shipment_status_enum, default=ShipmentStatus.CREADO, nullable=False, index=True
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["ShipmentItem"]] = relationship(
        back_populates="shipment", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["ShipmentStatusHistory"]] = relationship(
        back_populates="shipment", cascade="all, delete-orphan"
    )


class ShipmentItem(TimestampMixin, Base):
    __tablename__ = "shipment_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(10, 2), default=1, nullable=False)
    unidad: Mapped[str | None] = mapped_column(String(20), nullable=True)

    shipment: Mapped["Shipment"] = relationship(back_populates="items")


class ShipmentStatusHistory(Base):
    __tablename__ = "shipment_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    estado_anterior: Mapped[ShipmentStatus | None] = mapped_column(shipment_status_enum, nullable=True)
    estado_nuevo: Mapped[ShipmentStatus] = mapped_column(shipment_status_enum, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    gps_lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    shipment: Mapped["Shipment"] = relationship(back_populates="status_history")
