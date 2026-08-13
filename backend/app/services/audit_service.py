import uuid

from sqlalchemy.orm import Session

from app.models.misc import AuditLog


class AuditService:
    """Punto único de escritura en audit_logs (sección 37 del prompt).
    Cualquier endpoint que mute datos sensibles debe llamar a log_action."""

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        user_id: uuid.UUID | None,
        ip: str | None,
        accion: str,
        modulo: str,
        registro_id: str | None = None,
        valor_anterior: dict | None = None,
        valor_nuevo: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            ip=ip,
            accion=accion,
            modulo=modulo,
            registro_id=registro_id,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_logs(
        self, modulo: str | None = None, user_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[AuditLog]:
        query = self.db.query(AuditLog)
        if modulo:
            query = query.filter(AuditLog.modulo == modulo)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
