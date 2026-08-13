from app.workers.celery_app import celery_app


@celery_app.task(name="send_push_notification", bind=True, max_retries=3, default_retry_delay=10)
def send_push_notification_task(self, token: str, title: str, body: str, data: dict | None = None) -> dict:
    """Tarea de fondo: envía un push FCM a un token específico. Separada del
    ciclo request/response (ver docs/architecture.md sección 3) para no
    bloquear la API si Firebase está lento o caído."""
    from app.services.push_service import get_push_provider

    provider = get_push_provider()
    result = provider.send(token, title, body, data)
    return {"sent": result.sent, "detail": result.detail}


@celery_app.task(name="send_push_to_user", bind=True, max_retries=3, default_retry_delay=10)
def send_push_to_user(self, user_id: str, title: str, body: str, data: dict | None = None) -> dict:
    """Busca todos los device_tokens del usuario y envía el push a cada uno.
    Corre en un worker Celery separado, con su propia sesión de BD (no la del
    request que la originó)."""
    from app.db.session import SessionLocal
    from app.models.device_token import DeviceToken
    from app.services.push_service import get_push_provider

    db = SessionLocal()
    try:
        tokens = db.query(DeviceToken).filter(DeviceToken.user_id == user_id).all()
        provider = get_push_provider()
        results = [provider.send(t.token, title, body, data) for t in tokens]
        return {
            "tokens_found": len(tokens),
            "sent_count": sum(1 for r in results if r.sent),
        }
    finally:
        db.close()
