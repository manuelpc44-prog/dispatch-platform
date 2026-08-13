# Flujo Completo de GPS

## 1. Ciclo de vida en el chofer (Flutter)

```
INICIAR JORNADA
   → solicitar permisos (ubicación precisa + "siempre" en Android 10+)
   → verificar servicio de ubicación del sistema activo
   → crear driver_shift (POST /api/shifts/start) → recibe driver_shift_id
   → iniciar Foreground Service con notificación persistente
   → suscribirse a stream de posiciones (FusedLocationProvider vía plugin, ej. flutter_background_geolocation
     o geolocator + workmanager según se evalúe en Fase 11)
   → por cada posición: encolar en SQLite local (cola offline)
   → intentar flush de la cola cada N segundos si hay red
POSICIÓN RECIBIDA
   → validar accuracy mínima (descartar outliers > umbral configurable)
   → guardar local
   → si hay red: POST /api/tracking/location (batch, no una request por punto)
FINALIZAR JORNADA
   → flush final de la cola
   → POST /api/shifts/end
   → detener Foreground Service
```

## 2. Frecuencia de muestreo (estrategia por defecto, configurable en `system_settings`)

| Estado del vehículo         | Intervalo distancia | Intervalo tiempo máx. |
|------------------------------|---------------------|------------------------|
| En movimiento (> 5 km/h)     | cada 30–50 m         | 15 s                   |
| Detenido                     | —                    | 60 s (heartbeat)        |
| Batería baja (<15%)          | —                    | 120 s (modo ahorro)     |

Combinar ambos criterios (distancia OR tiempo, lo que ocurra primero) evita tanto flooding
en tramos rectos rápidos como silencio prolongado en semáforos/tacos.

## 3. Cola offline y anti-duplicados

- Cada posición generada en el dispositivo lleva un `client_uuid` (UUID v4 generado en Flutter).
- El backend aplica `INSERT ... ON CONFLICT (client_uuid) DO NOTHING` en `gps_positions`,
  haciendo el endpoint idempotente ante reintentos de sincronización.
- El envío es por lotes (`POST /api/tracking/location` acepta un array), reduciendo overhead
  de red cuando el dispositivo recupera conectividad tras varios minutos offline.

## 4. Backend → PostgreSQL → Redis → WebSocket

```
POST /api/tracking/location (batch)
   → validar pertenencia: driver_shift_id activo y del chofer autenticado
   → INSERT en gps_positions (idempotente por client_uuid)
   → actualizar "posición en vivo" en Redis: SET live:driver:{driver_id} {lat,lng,...} EX 120
   → PUBLISH al canal Redis "gps:dispatcher:{dispatcher_id}" y "gps:tracking:{tracking_code}"
   → evaluar geocercas (llegada a cliente / llegada a bodega) → si corresponde, dispara
     ShipmentStateService.transition(...)
WebSocket Hub (proceso backend, suscrito a Redis Pub/Sub)
   → recibe el mensaje publicado
   → reenvía a todas las conexiones WS abiertas en ese canal (fan-out)
Frontend (React)
   → onmessage → actualiza posición del marcador en el mapa (sin recargar, sin F5)
```

Redis Pub/Sub es necesario (no bastan WebSockets en memoria) porque el backend puede correr
en múltiples réplicas detrás de Nginx; una posición ingerida por la réplica A debe poder
llegar a un despachador conectado por WebSocket a la réplica B.

## 5. Diferenciación de conceptos GPS (obligatorio, sección 57 del prompt)

| Concepto            | Tabla / fuente                          | Vida útil                     |
|----------------------|------------------------------------------|--------------------------------|
| GPS del chofer       | `gps_positions.driver_shift_id`          | duración de la jornada         |
| GPS del despacho     | `gps_positions.route_stop_id` (nullable) | mientras ese stop está activo  |
| Historial GPS        | `gps_positions` completa                 | permanente (particionada por fecha) |
| Posición en vivo      | Redis `live:driver:{id}`                 | TTL 120 s, se sobreescribe      |

## 6. Estados de conexión detectados

```
ONLINE          → última posición recibida hace < 30 s
OFFLINE         → sin posiciones hace > umbral configurable (ej. 90 s) con jornada activa
GPS_DISABLED    → la app reporta explícitamente que el usuario desactivó el GPS
GPS_ACTIVE      → foreground service corriendo y emitiendo
LOW_ACCURACY    → accuracy reportada > umbral (ej. 50 m), se muestra advertencia en el mapa
```

Se calcula en backend (no confiar en que el frontend infiera "offline" localmente) comparando
`now() - live:driver:{id}.received_at` contra los umbrales de `system_settings`.
