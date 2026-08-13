# Plan de Desarrollo por Fases

Se sigue estrictamente el orden de fases del prompt maestro (secciones 51 y 62). Cada fase se
entrega solo cuando la anterior está probada y funcionando, con el reporte del protocolo de
la sección 52 (Fase / Estado / Archivos / Funcionalidades / Pruebas / Resultado / Pendientes /
Siguiente fase).

| Fase | Entregable central | Criterio de cierre |
|---|---|---|
| 0 | Análisis y arquitectura (este documento) | Confirmación del usuario |
| 1 | Docker Compose, Postgres, Redis, backend/frontend "hello world" | `docker compose up -d` levanta todo sin errores |
| 2 | Modelos SQLAlchemy + Alembic + seed | Migraciones aplican limpio, seed carga datos de prueba |
| 3 | Auth JWT + roles + permisos | Login funcional para los 5 roles, refresh token probado |
| 4 | Clientes + direcciones múltiples | CRUD probado, geocodificación básica |
| 5 | Vehículos y choferes | CRUD + estados probados |
| 6 | Despachos (CRUD + máquina de estados) | Transiciones válidas/ inválidas cubiertas por tests |
| 7 | Rutas y asignación múltiple | Asignar N despachos a un chofer, reordenar stops |
| 8 | GPS backend + WebSocket | Posición llega de un cliente de prueba al panel en <2s |
| 9 | Panel despachador (mapa en vivo) | Ver choferes simultáneos en mapa real |
| 10 | App Android base (Flutter) | Login + listado de despachos funcional |
| 11 | GPS Android (foreground/background) | Tracking sobrevive con pantalla apagada, cola offline probada |
| 12 | Entregas (firma, foto, incidencias) | Flujo completo de entrega registrado con evidencia |
| 13 | Portal cliente | Seguimiento en vivo por tracking_code, sin exponer otros datos |
| 14 | Notificaciones FCM | Push recibido en los eventos clave del despacho |
| 15 | Historial y reportes | Reproducción de ruta funcional |
| 16 | Auditoría de seguridad | Revisión de permisos y endpoints |
| 17 | Testing integral | Suite completa backend/frontend/Android en verde |
| 18 | Producción (Nginx, HTTPS, backups) | Prueba de aceptación end-to-end (sección 61) exitosa |

## Cierre de Fase 0

Entregados: `architecture.md`, `database.md` (+ ERD), `rbac.md`, `states.md` (+ diagrama de
transiciones), `gps.md`, `structure.md`, `dependencies.md`, `risks-security-scalability.md`,
este `roadmap.md`, y el esqueleto de carpetas del repositorio (sin código todavía, según
regla explícita del prompt de no implementar antes de la confirmación).

Pendiente antes de Fase 1: confirmación del usuario para comenzar infraestructura (Docker
Compose + servicios base).
