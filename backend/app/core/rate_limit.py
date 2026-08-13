"""Rate limiting por ventana fija, usando Redis (ver docs/risks-security-
scalability.md — prometido desde Fase 0, implementado en Fase 16).

Para login se cuentan solo los intentos FALLIDOS, nunca los exitosos — así un
usuario legítimo que inicia sesión varias veces seguidas (o una suite de
tests) nunca se autobloquea; solo se limita a quien está adivinando
contraseñas."""

import redis

from app.core.config import settings
from app.core.exceptions import DomainError
from fastapi import status


class RateLimitExceeded(DomainError):
    def __init__(self, retry_after_seconds: int):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=f"Demasiados intentos. Intenta de nuevo en {retry_after_seconds} segundos.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


def _get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url)


def check_rate_limit(key: str, max_attempts: int, window_seconds: int) -> None:
    """Ventana fija simple: cuenta CADA llamada a esta función como un intento
    (usar para endpoints donde todo intento —exitoso o no— debe contar, como
    /tracking/location). Falla abierto si Redis no está disponible."""
    try:
        r = _get_redis_client()
        try:
            current = r.incr(key)
            if current == 1:
                r.expire(key, window_seconds)
            if current > max_attempts:
                ttl = r.ttl(key)
                raise RateLimitExceeded(retry_after_seconds=max(ttl, 1))
        finally:
            r.close()
    except redis.RedisError:
        pass


def check_failed_attempts(key: str, max_attempts: int) -> None:
    """Antes de intentar autenticar: si ya se superó max_attempts fallidos
    recientes para esta key, bloquea con 429 sin siquiera tocar la BD."""
    try:
        r = _get_redis_client()
        try:
            current = r.get(key)
            if current and int(current) >= max_attempts:
                ttl = r.ttl(key)
                raise RateLimitExceeded(retry_after_seconds=max(ttl, 1))
        finally:
            r.close()
    except redis.RedisError:
        pass


def register_failed_attempt(key: str, window_seconds: int) -> None:
    """Login inválido: incrementa el contador de fallos (con expiración)."""
    try:
        r = _get_redis_client()
        try:
            current = r.incr(key)
            if current == 1:
                r.expire(key, window_seconds)
        finally:
            r.close()
    except redis.RedisError:
        pass


def reset_failed_attempts(key: str) -> None:
    """Login exitoso: limpia el contador de fallos para esta key."""
    try:
        r = _get_redis_client()
        try:
            r.delete(key)
        finally:
            r.close()
    except redis.RedisError:
        pass
