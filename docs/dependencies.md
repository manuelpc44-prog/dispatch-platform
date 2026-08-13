# Dependencias Principales

## Backend (Python 3.12+)

| Paquete | Uso |
|---|---|
| fastapi | framework API |
| uvicorn[standard] | servidor ASGI |
| sqlalchemy 2.x | ORM |
| alembic | migraciones |
| pydantic v2 / pydantic-settings | validación y configuración |
| psycopg[binary] | driver PostgreSQL |
| python-jose[cryptography] | JWT |
| passlib[bcrypt] | hashing de contraseñas |
| redis | cliente Redis (pub/sub, cache) |
| celery | tareas en segundo plano |
| websockets | soporte WS (vía FastAPI/Starlette) |
| httpx | llamadas a OSRM/ORS y FCM |
| pytest, pytest-asyncio, httpx (test client) | testing |

## Frontend

| Paquete | Uso |
|---|---|
| react, react-dom | UI |
| typescript | tipado |
| vite | build/dev server |
| react-router-dom | ruteo |
| axios o fetch tipado | cliente API |
| maplibre-gl o leaflet | mapa |
| socket-like client nativo (`WebSocket` API) | tiempo real |
| zustand o @reduxjs/toolkit | estado global (a decidir en Fase 9 según complejidad real) |
| tailwindcss | estilos |

## Mobile (Flutter)

| Paquete | Uso |
|---|---|
| geolocator / flutter_background_geolocation | GPS (a evaluar en Fase 11 por consumo de batería vs. confiabilidad en background) |
| flutter_foreground_task | foreground service Android |
| sqflite | cola offline local |
| dio | cliente HTTP |
| web_socket_channel | tiempo real |
| firebase_messaging | push notifications |
| provider o riverpod | manejo de estado |
| flutter_map o mapbox_gl | mapa embebido |

## Infraestructura

Docker, Docker Compose, Nginx, PostgreSQL 16+ (con PostGIS opcional para consultas
geoespaciales avanzadas — evaluar en Fase 2 si el cálculo de distancias vía `ST_Distance`
aporta frente a fórmula haversine en aplicación), Redis 7+.

Nota: el prompt original no exige PostGIS; se deja como decisión abierta para Fase 2 según
si se requieren consultas geoespaciales complejas en BD (geocercas, radios) o basta con
cálculos en la capa de servicios.
