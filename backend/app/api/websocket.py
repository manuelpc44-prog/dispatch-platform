import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import selectinload

from app.core.security import InvalidTokenError, decode_token
from app.db.session import SessionLocal
from app.models.user import User
from app.websocket.manager import dispatcher_manager, tracking_manager

router = APIRouter(tags=["websocket"])


def _authorize_dispatcher(token: str) -> bool:
    """Valida el JWT y el rol fuera del ciclo normal de dependencias de FastAPI,
    porque los WebSocket no pasan por Depends(get_current_user) de la misma forma
    (el token llega por query param, no por header Authorization)."""
    try:
        payload = decode_token(token, expected_type="access")
    except InvalidTokenError:
        return False

    db = SessionLocal()
    try:
        user_id = uuid.UUID(payload.get("sub"))
        user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            return False
        role_names = {r.name for r in user.roles}
        return bool(role_names.intersection({"ADMINISTRADOR", "DESPACHADOR"}))
    except (TypeError, ValueError):
        return False
    finally:
        db.close()


@router.websocket("/ws/dispatcher")
async def ws_dispatcher(websocket: WebSocket, token: str = Query(...)) -> None:
    if not _authorize_dispatcher(token):
        await websocket.close(code=4401)
        return

    await dispatcher_manager.connect(websocket)
    try:
        while True:
            # No esperamos mensajes del cliente en este canal; solo mantenemos viva
            # la conexión. Si el cliente cierra, WebSocketDisconnect lo captura abajo.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await dispatcher_manager.disconnect(websocket)


@router.websocket("/ws/tracking/{tracking_code}")
async def ws_tracking(websocket: WebSocket, tracking_code: str) -> None:
    # Público — sin autenticación, el tracking_code (UUID no adivinable) es la
    # protección (ver docs/rbac.md regla 4).
    await tracking_manager.connect(tracking_code, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await tracking_manager.disconnect(tracking_code, websocket)
