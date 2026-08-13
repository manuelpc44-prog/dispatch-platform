# Arquitectura General — Plataforma de Despachos, Rutas y GPS

## 1. Visión

Sistema distribuido de 4 capas físicas (BD → Backend → Frontend/Móvil → Cliente final)
comunicadas por REST + WebSocket, con un pipeline de posiciones GPS que fluye desde el
dispositivo del chofer hasta el mapa en vivo del despachador y del cliente.

## 2. Estilo arquitectónico

- **Backend**: Clean Architecture por capas dentro de FastAPI:
  - `api/` — routers HTTP y WebSocket (adaptadores de entrada, sin lógica de negocio)
  - `services/` — casos de uso / lógica de negocio (máquina de estados, asignación, RBAC)
  - `repositories/` — acceso a datos vía SQLAlchemy (aísla el ORM de los servicios)
  - `models/` — entidades ORM (SQLAlchemy)
  - `schemas/` — contratos Pydantic (entrada/salida de API, separados de los modelos ORM)
  - `core/` — configuración, seguridad (JWT), settings, excepciones comunes
  - `websocket/` — gestor de conexiones y difusión de eventos en tiempo real
  - `workers/` — tareas asíncronas (Celery): notificaciones, cálculo de rutas, limpieza
- **Frontend**: React + TS, arquitectura por features (páginas que consumen `services/`
  tipados, estado compartido en `stores/` — Zustand o Redux Toolkit a definir en Fase 9).
- **Mobile**: Flutter con patrón Repository + Provider, capa de servicios GPS aislada del
  resto de la UI para poder testear el foreground service de forma independiente.

## 3. Componentes y flujo de datos

```
[Flutter App Chofer]
   │  GPS (foreground service)
   │  REST (auth, despachos, entregas) + cola offline (SQLite local)
   ▼
[FastAPI Backend] ──▶ [PostgreSQL]          (persistencia transaccional)
   │        └──────▶ [Redis]                (pub/sub, cache, rate limiting, Celery broker)
   │
   ├─ WebSocket Hub ──▶ [Panel Despachador React]   (mapa en vivo)
   │                 └▶ [Portal Cliente React]      (seguimiento por tracking_code)
   │
   └─ Celery Workers ─▶ [Firebase Cloud Messaging]  (push notifications)
                     └▶ [OSRM/ORS/GraphHopper]       (cálculo de rutas, vía capa de abstracción)
```

## 4. Principio de separación GPS (crítico, ver sección 57 del prompt)

Se modelan **cuatro conceptos GPS distintos y no intercambiables**:

1. **GPS del chofer** — posiciones ligadas a una jornada activa (`driver_shift_id`).
2. **GPS del despacho** — posiciones asociadas a un `shipment_id`/`route_stop_id` específico
   dentro de esa jornada (permite reconstruir "dónde estaba el vehículo cuando iba hacia el
   cliente X").
3. **Historial GPS** — la tabla `gps_positions` completa, append-only, usada para reproducción.
4. **Posición en vivo** — una fila derivada (Redis, TTL corto) con la última posición conocida
   por `driver_id`; se sobreescribe, no se acumula. Es lo que consulta el mapa en tiempo real
   para no golpear PostgreSQL en cada refresco.

## 5. Comunicación en tiempo real

WebSocket con canales por rol:
- `ws/dispatcher/{dispatcher_id}` — recibe todas las posiciones de choferes bajo su gestión.
- `ws/tracking/{tracking_code}` — canal público de un despacho específico, sin exponer otros
  despachos ni choferes (autorización por token de tracking, no por sesión de usuario).
- `ws/driver/{driver_id}` — canal privado para reasignaciones/instrucciones al chofer en curso.

Redis Pub/Sub desacopla la ingesta de GPS (alto volumen, escrituras) de la difusión WebSocket
(lectura, fan-out), permitiendo escalar el backend a múltiples instancias sin perder eventos.

## 6. Capa de abstracción de mapas y ruteo

- Interfaz `MapProvider` (backend) y `RouteProvider` con implementación inicial OSM/MapLibre +
  OSRM. Cambiar de proveedor implica implementar la interfaz, no tocar los servicios que la
  consumen (Strategy pattern).

## 7. Multi-tenencia de datos por rol

Toda consulta pasa por un filtro de autorización a nivel de repositorio (no solo en el router):
un `CLIENTE` autenticado solo puede ejecutar queries con `customer_id = current_user.customer_id`
inyectado por el propio repositorio, nunca confiando en el filtro que envíe el frontend.
