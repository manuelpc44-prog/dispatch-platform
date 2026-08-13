import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin


class DeviceToken(TimestampMixin, Base):
    """Token FCM de un dispositivo del usuario. No estaba en el diseño mínimo de
    tablas de docs/database.md (sección 32 del prompt) — se agrega en Fase 14
    porque es imprescindible para poder enviar push dirigidos a un usuario."""

    __tablename__ = "device_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), default="android", nullable=False)
