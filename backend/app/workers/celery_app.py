import os

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "dispatch_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.notification_worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Santiago",
    enable_utc=True,
    # En tests (ver tests/conftest.py) se ejecuta en modo "eager": las tareas
    # corren en el mismo proceso, sin necesitar un worker Celery separado
    # consumiendo de Redis. En producción esto queda en False (default).
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true",
    task_eager_propagates=True,
)
