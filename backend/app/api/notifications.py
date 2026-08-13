import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import DomainError
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import DeviceTokenRegister, NotificationOut
from app.services.notification_service import DeviceTokenService, NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationNotFound(DomainError):
    def __init__(self):
        super().__init__("NOTIFICATION_NOT_FOUND", "Notificación no encontrada", status.HTTP_404_NOT_FOUND)


@router.post("/register-device", status_code=201)
def register_device(
    payload: DeviceTokenRegister, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict:
    DeviceTokenService(db).register(current_user.id, payload.token, payload.platform)
    return {"status": "registered"}


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[NotificationOut]:
    return NotificationService(db).list_for_user(current_user.id, unread_only=unread_only)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> NotificationOut:
    notification = NotificationService(db).mark_read(notification_id, current_user.id)
    if notification is None:
        raise NotificationNotFound()
    return notification
