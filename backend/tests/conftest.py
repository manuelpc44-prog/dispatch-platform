import os

# Debe fijarse ANTES de cualquier import de app.* que termine cargando
# app.workers.celery_app, para que las tareas corran en el mismo proceso
# durante los tests (sin necesitar un worker Celery separado).
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"


def _flush_rate_limit_keys():
    """Los tests reutilizan las mismas cuentas de prueba (ej. admin@...) muchas
    veces dentro de la misma ventana de rate limiting real (Fase 16). Sin este
    flush, la propia suite de tests se autobloquearía con 429 — no es un bug
    del rate limiter, es que producción y tests comparten la misma protección."""
    import redis

    from app.core.config import settings

    try:
        r = redis.Redis.from_url(settings.redis_url)
        for key in r.scan_iter("ratelimit:*"):
            r.delete(key)
        r.close()
    except Exception:
        pass


_flush_rate_limit_keys()
