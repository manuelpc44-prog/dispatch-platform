import uuid

from sqlalchemy.orm import Session

from app.models.device_token import DeviceToken
from app.models.misc import Notification
from app.models.user import User


class NotificationService:
    """Punto único desde el que el resto del backend dispara notificaciones.
    Siempre crea el registro in-app (tabla notifications); el push real se
    delega a Celery para no bloquear el request que la origina (ver
    docs/architecture.md sección 3 — Celery separa I/O externo lento del
    ciclo request/response)."""

    def __init__(self, db: Session):
        self.db = db

    def notify_user(self, user_id: uuid.UUID, tipo: str, titulo: str, cuerpo: str, data: dict | None = None) -> Notification:
        notification = Notification(user_id=user_id, tipo=tipo, titulo=titulo, cuerpo=cuerpo, leido=False)
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        from app.workers.notification_worker import send_push_to_user

        send_push_to_user.delay(str(user_id), titulo, cuerpo, data or {})

        return notification

    def notify_customer_of_shipment(self, shipment, tipo: str, titulo: str, cuerpo: str) -> None:
        from app.models.customer import Customer

        customer = self.db.query(Customer).filter(Customer.id == shipment.customer_id).first()
        if customer and customer.user_id:
            self.notify_user(customer.user_id, tipo, titulo, cuerpo, {"shipment_id": str(shipment.id)})

    def notify_dispatchers(self, tipo: str, titulo: str, cuerpo: str, data: dict | None = None) -> None:
        from app.models.user import Role, user_roles

        dispatcher_users = (
            self.db.query(User)
            .join(user_roles, User.id == user_roles.c.user_id)
            .join(Role, Role.id == user_roles.c.role_id)
            .filter(Role.name.in_(["ADMINISTRADOR", "DESPACHADOR"]))
            .all()
        )
        for user in dispatcher_users:
            self.notify_user(user.id, tipo, titulo, cuerpo, data)

    def list_for_user(self, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.leido.is_(False))
        return query.order_by(Notification.created_at.desc()).limit(100).all()

    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification | None:
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if notification:
            notification.leido = True
            self.db.commit()
            self.db.refresh(notification)
        return notification


class DeviceTokenService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, user_id: uuid.UUID, token: str, platform: str) -> DeviceToken:
        existing = self.db.query(DeviceToken).filter(DeviceToken.token == token).first()
        if existing:
            existing.user_id = user_id
            existing.platform = platform
            self.db.commit()
            self.db.refresh(existing)
            return existing

        device_token = DeviceToken(user_id=user_id, token=token, platform=platform)
        self.db.add(device_token)
        self.db.commit()
        self.db.refresh(device_token)
        return device_token

    def unregister(self, token: str, user_id: uuid.UUID) -> None:
        self.db.query(DeviceToken).filter(
            DeviceToken.token == token, DeviceToken.user_id == user_id
        ).delete()
        self.db.commit()
