# Riesgos Técnicos, Seguridad y Escalabilidad

## Riesgos técnicos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| GPS en background de Android es frágil (Doze mode, fabricantes con restricciones agresivas tipo Xiaomi/Huawei) | Pérdida de tracking, mala UX | Foreground Service + notificación persistente + guía al usuario para whitelisting de batería; probar en dispositivos reales de gama media, no solo emulador |
| Volumen de `gps_positions` crece rápido (miles de filas/jornada/chofer) | Degradación de queries de mapa en vivo e historial | Partición por fecha, índices compuestos, la "posición en vivo" se sirve desde Redis, no desde PostgreSQL |
| WebSocket con múltiples réplicas backend | Un despachador conectado a la réplica equivocada no recibe eventos | Redis Pub/Sub como bus compartido entre réplicas (ya contemplado en arquitectura) |
| Proveedor de ruteo externo (OSRM/ORS) caído o con rate limit | Bloquea asignación/cálculo de ETA | Capa de abstracción `RouteProvider` + timeout corto + degradar a línea recta/ETA estimado si falla, sin bloquear el flujo operativo |
| Offline prolongado del chofer (zonas rurales) | Cola local crece, riesgo de pérdida de datos si se desinstala la app | Cola en SQLite con límite razonable y purga solo tras confirmación de sync exitosa |
| Máquina de estados con transiciones inválidas por bugs de concurrencia (dos eventos casi simultáneos) | Estado inconsistente del despacho | Transacción + `SELECT ... FOR UPDATE` sobre el shipment al transicionar, validación server-side única fuente de verdad |
| Alcance muy amplio del proyecto (todo el prompt en una sola sesión) | Entregar código no probado o inconsistente | Desarrollo estrictamente por fases con pruebas antes de avanzar, como exige el propio prompt |

## Estrategia de seguridad

- JWT de acceso de vida corta (15-30 min) + refresh token de vida más larga, almacenado
  httpOnly cookie en frontend web y almacenamiento seguro (`flutter_secure_storage`) en
  Android.
- RBAC validado en backend en cada request (ver `rbac.md`), nunca confiando en el rol que
  declare el cliente.
- Rate limiting en endpoints sensibles (`/auth/login`, `/tracking/location`) vía Redis
  (sliding window) para mitigar fuerza bruta y flooding de posiciones falsas.
- CORS restringido a los orígenes declarados en `.env` (panel despachador, portal cliente).
- Passwords con bcrypt (passlib), nunca en texto plano ni en logs.
- Auditoría (`audit_logs`) en toda mutación sensible: usuarios, roles, asignaciones,
  cambios de estado.
- HTTPS obligatorio en producción (Nginx + Let's Encrypt), HSTS.
- El `tracking_code` del portal cliente es un UUID v4 no secuencial — impide enumeración de
  despachos ajenos.
- Secrets nunca en el repositorio: `.env.example` con placeholders, `.env` real en
  `.gitignore`.

## Estrategia de escalabilidad

- Backend stateless (JWT sin sesión en servidor) → horizontal scaling directo detrás de
  Nginx/load balancer.
- Redis como punto de coordinación entre réplicas (Pub/Sub para WS, cache de posición en
  vivo, broker de Celery) — es el único componente que requiere ser compartido.
- Particionamiento de `gps_positions` por rango de fecha desde el inicio del diseño (aunque
  la partición física se implemente cuando el volumen lo justifique, en Fase 2 se deja el
  modelo preparado).
- Celery separa trabajo pesado (envío de notificaciones FCM, recálculo de rutas) del ciclo
  request/response, evitando que la ingesta de GPS se vea afectada por I/O externo lento.
- Cálculo de rutas (OSRM) puede correr como servicio propio y escalarse independientemente
  del backend principal si el volumen de despachos lo requiere.
