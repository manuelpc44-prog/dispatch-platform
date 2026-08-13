import asyncio
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.admin_example import router as admin_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.customers import router as customers_router
from app.api.deliveries import incidents_router, router as deliveries_router
from app.api.fleet import drivers_router, vehicles_router, warehouses_router
from app.api.gps import shifts_router, tracking_router
from app.api.health import router as health_router
from app.api.notifications import router as notifications_router
from app.api.reports import router as reports_router
from app.api.routes import router as routes_router
from app.api.shipments import public_router as public_tracking_router, router as shipments_router
from app.api.websocket import router as websocket_router
from app.core.config import settings
from app.websocket.manager import redis_listener_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    listener = asyncio.create_task(redis_listener_task(settings.redis_url))
    yield
    listener.cancel()
    try:
        await listener
    except asyncio.CancelledError:
        pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_media_dir = pathlib.Path("/tmp/dispatch-uploads")
_media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media_dir)), name="media")

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(customers_router, prefix="/api")
app.include_router(vehicles_router, prefix="/api")
app.include_router(drivers_router, prefix="/api")
app.include_router(warehouses_router, prefix="/api")
app.include_router(shipments_router, prefix="/api")
app.include_router(public_tracking_router, prefix="/api")
app.include_router(routes_router, prefix="/api")
app.include_router(shifts_router, prefix="/api")
app.include_router(tracking_router, prefix="/api")
app.include_router(deliveries_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(websocket_router)


@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "environment": settings.environment}
