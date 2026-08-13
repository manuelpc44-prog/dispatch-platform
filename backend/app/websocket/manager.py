"""Gestor de conexiones WebSocket. Ver docs/gps.md sección 4 y docs/architecture.md
sección 5: Redis Pub/Sub desacopla la ingesta de GPS (escrituras) de la difusión
WebSocket (lectura, fan-out), permitiendo múltiples réplicas de backend."""

import asyncio
import json
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class DispatcherConnectionManager:
    """Canal ws/dispatcher: cualquier ADMINISTRADOR/DESPACHADOR ve todos los choferes
    (ver docs/rbac.md — no hay scoping adicional por despachador en este alcance)."""

    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        async with self._lock:
            targets = list(self._connections)
        dead = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    @property
    def active_count(self) -> int:
        return len(self._connections)


class TrackingConnectionManager:
    """Canal ws/tracking/{tracking_code}: público, un cliente solo recibe eventos de
    SU despacho (el tracking_code no adivinable es la protección, ver docs/rbac.md regla 4)."""

    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, tracking_code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[tracking_code].add(websocket)

    async def disconnect(self, tracking_code: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[tracking_code].discard(websocket)
            if not self._connections[tracking_code]:
                del self._connections[tracking_code]

    async def broadcast(self, tracking_code: str, message: dict) -> None:
        async with self._lock:
            targets = list(self._connections.get(tracking_code, set()))
        dead = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections[tracking_code].discard(ws)

    @property
    def active_channels(self) -> int:
        return len(self._connections)


dispatcher_manager = DispatcherConnectionManager()
tracking_manager = TrackingConnectionManager()


async def redis_listener_task(redis_url: str) -> None:
    """Tarea de fondo: se suscribe a los canales Redis publicados por el endpoint de
    ingesta GPS y reenvía (fan-out) a las conexiones WebSocket abiertas. Ver
    docs/gps.md sección 4."""
    import redis.asyncio as aioredis

    redis_client = aioredis.from_url(redis_url)
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe("gps:dispatcher:*", "gps:tracking:*")
    try:
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            try:
                channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                data = json.loads(message["data"])
            except Exception:
                logger.exception("Mensaje Redis Pub/Sub malformado, se ignora")
                continue

            if channel.startswith("gps:dispatcher:"):
                await dispatcher_manager.broadcast(data)
            elif channel.startswith("gps:tracking:"):
                tracking_code = channel.split(":", 2)[-1]
                await tracking_manager.broadcast(tracking_code, data)
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.aclose()
        await redis_client.aclose()
