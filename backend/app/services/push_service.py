"""Capa de abstracción de push notifications (mismo patrón Strategy que
geocoding.py en Fase 4). Ver instrucciones de configuración al final de este
archivo y en .env.example."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PushResult:
    sent: bool
    detail: str


class PushProvider(ABC):
    @abstractmethod
    def send(self, token: str, title: str, body: str, data: dict | None = None) -> PushResult:
        raise NotImplementedError


class NullPushProvider(PushProvider):
    """Se usa cuando no hay credenciales de Firebase configuradas. No falla el
    flujo de negocio (crear un despacho no debe romperse porque falte FCM) —
    solo registra en log que el push no se envió realmente."""

    def send(self, token: str, title: str, body: str, data: dict | None = None) -> PushResult:
        logger.info(
            "FCM no configurado — push NO enviado (modo desarrollo). "
            "title=%r body=%r token=%s...",
            title,
            body,
            token[:12],
        )
        return PushResult(sent=False, detail="FCM_NOT_CONFIGURED")


class FirebasePushProvider(PushProvider):
    def __init__(self, credentials_path: str):
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)

    def send(self, token: str, title: str, body: str, data: dict | None = None) -> PushResult:
        from firebase_admin import messaging

        message = messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
        )
        try:
            message_id = messaging.send(message)
            return PushResult(sent=True, detail=message_id)
        except Exception as exc:  # noqa: BLE001 — nunca debe tumbar el flujo de negocio
            logger.exception("Error enviando push FCM")
            return PushResult(sent=False, detail=str(exc))


_provider: PushProvider | None = None


def get_push_provider() -> PushProvider:
    global _provider
    if _provider is not None:
        return _provider

    if settings.fcm_credentials:
        try:
            _provider = FirebasePushProvider(settings.fcm_credentials)
            logger.info("FCM inicializado con credenciales reales (%s)", settings.fcm_credentials)
        except Exception:
            logger.exception(
                "No se pudo inicializar Firebase con FCM_CREDENTIALS=%s — usando NullPushProvider",
                settings.fcm_credentials,
            )
            _provider = NullPushProvider()
    else:
        _provider = NullPushProvider()

    return _provider


# ---------------------------------------------------------------------------
# CÓMO INTEGRAR CREDENCIALES REALES DE FIREBASE
# ---------------------------------------------------------------------------
# 1. En Firebase Console (https://console.firebase.google.com/):
#    - Crea o abre tu proyecto.
#    - Ve a "Configuración del proyecto" (ícono de engranaje) → pestaña
#      "Cuentas de servicio" ("Service accounts").
#    - Haz clic en "Generar nueva clave privada" ("Generate new private key").
#      Esto descarga un archivo JSON (ej. mi-proyecto-firebase-adminsdk-xxxx.json).
#
# 2. NO subas ese archivo al repositorio (agrégalo a .gitignore si lo copias
#    dentro del proyecto). Dos formas de usarlo:
#
#    a) Desarrollo local (fuera de Docker):
#       - Copia el archivo a, por ejemplo, backend/secrets/firebase-adminsdk.json
#       - En tu .env (no en .env.example): FCM_CREDENTIALS=./secrets/firebase-adminsdk.json
#
#    b) Docker / producción:
#       - Monta el archivo como volumen de solo lectura en docker-compose.yml,
#         por ejemplo:
#           backend:
#             volumes:
#               - ./secrets/firebase-adminsdk.json:/run/secrets/firebase-adminsdk.json:ro
#         y en .env: FCM_CREDENTIALS=/run/secrets/firebase-adminsdk.json
#       - O usar un secret manager (AWS Secrets Manager, GCP Secret Manager,
#         Docker Swarm secrets) que escriba el JSON a esa misma ruta al arrancar
#         el contenedor.
#
# 3. Reinicia el backend. Al arrancar, si FCM_CREDENTIALS apunta a un archivo
#    válido, se usará FirebasePushProvider automáticamente — no hay que tocar
#    código. Si la variable no está seteada o el archivo no es válido, el
#    sistema sigue funcionando con NullPushProvider (los pushes solo se
#    registran en el log, nunca se envían) — así el resto de la plataforma
#    no depende de tener Firebase configurado para funcionar.
#
# 4. Verificación rápida una vez configurado:
#       curl -X POST http://localhost:8000/api/notifications/register-device \
#         -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
#         -d '{"token": "<un_token_FCM_real_de_un_dispositivo>", "platform": "android"}'
#    y luego dispara cualquier evento que notifique a ese usuario (ej. una
#    transición de estado de despacho) — debería llegar la notificación al
#    dispositivo real en vez de solo quedar en el log.
# ---------------------------------------------------------------------------
