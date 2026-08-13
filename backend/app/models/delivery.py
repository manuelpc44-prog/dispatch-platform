import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import DeliveryResult, EvidenceType
from app.models.mixins import TimestampMixin

delivery_result_enum = PGEnum(DeliveryResult, name="delivery_result", create_type=True)
evidence_type_enum = PGEnum(EvidenceType, name="evidence_type", create_type=True)


class Delivery(TimestampMixin, Base):
    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    receptor_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resultado: Mapped[DeliveryResult] = mapped_column(delivery_result_enum, nullable=False)
    motivo_fallo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gps_lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidence: Mapped[list["DeliveryEvidence"]] = relationship(
        back_populates="delivery", cascade="all, delete-orphan"
    )


class DeliveryEvidence(TimestampMixin, Base):
    __tablename__ = "delivery_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[EvidenceType] = mapped_column(evidence_type_enum, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    delivery: Mapped["Delivery"] = relationship(back_populates="evidence")
