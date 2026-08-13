import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import Forbidden, InactiveUser, InvalidToken
from app.core.security import InvalidTokenError, decode_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise InvalidToken("No se proporcionó token de autenticación")
    try:
        payload = decode_token(token, expected_type="access")
    except InvalidTokenError as exc:
        raise InvalidToken(str(exc)) from exc

    user_id = payload.get("sub")
    try:
        user_uuid = uuid.UUID(user_id)
    except (TypeError, ValueError):
        raise InvalidToken("Token con subject inválido")

    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.id == user_uuid)
        .first()
    )
    if user is None:
        raise InvalidToken("Usuario del token ya no existe")
    if not user.is_active:
        raise InactiveUser()
    return user


def require_role(*allowed_roles: str):
    """Dependencia parametrizable: require_role('ADMINISTRADOR', 'DESPACHADOR')."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role_names = {r.name for r in current_user.roles}
        if not user_role_names.intersection(allowed_roles):
            raise Forbidden(
                f"Requiere uno de estos roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return dependency
