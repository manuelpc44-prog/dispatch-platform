import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShiftSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    driver_id: uuid.UUID
    driver_name: str
    vehicle_id: uuid.UUID
    vehicle_plate: str
    estado: str
    iniciada_at: datetime | None
    finalizada_at: datetime | None
    distancia_km: float
    duracion_minutos: float | None
    despachos_count: int
    entregados_count: int


class RoutePositionOut(BaseModel):
    latitude: float
    longitude: float
    speed: float | None
    recorded_at: datetime


class DashboardStats(BaseModel):
    despachos_hoy: int
    en_preparacion: int
    asignados: int
    en_ruta: int
    entregados: int
    no_entregados: int
    incidencias: int
    choferes_activos: int
    vehiculos_activos: int
    distancia_recorrida_km_hoy: float
    tiempo_promedio_entrega_minutos: float | None
