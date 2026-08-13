import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.exceptions import InactiveUser, InvalidCredentials, InvalidToken
from app.core.rate_limit import check_failed_attempts, register_failed_attempt, reset_failed_attempts
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User) -> TokenResponse:
    role_names = [r.name for r in user.roles]
    return TokenResponse(
        access_token=create_access_token(str(user.id), role_names),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"ratelimit:login:ip:{client_ip}"
    email_key = f"ratelimit:login:email:{payload.email}"

    # Se bloquea ANTES de tocar la BD si ya hay demasiados fallos recientes.
    # Los intentos EXITOSOS nunca cuentan para este límite (ver rate_limit.py) —
    # así un usuario legítimo logueándose varias veces seguidas nunca se
    # autobloquea; solo quien está adivinando contraseñas.
    check_failed_attempts(ip_key, max_attempts=30)
    check_failed_attempts(email_key, max_attempts=5)

    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.email == payload.email)
        .first()
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        register_failed_attempt(ip_key, window_seconds=60)
        register_failed_attempt(email_key, window_seconds=60)
        raise InvalidCredentials()
    if not user.is_active:
        raise InactiveUser()

    reset_failed_attempts(email_key)
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise InvalidToken(str(exc)) from exc

    try:
        user_uuid = uuid.UUID(token_payload.get("sub"))
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
    return _issue_tokens(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        roles=[r.name for r in current_user.roles],
    )
