# Auditoría de Seguridad — Fase 16

Revisión de permisos, autenticación, endpoints, datos y logs, según la
sección 16 del prompt maestro (Fase 16: "Auditar: permisos, autenticación,
endpoints, datos, logs").

## 1. Autenticación

- ✅ Contraseñas con bcrypt (`passlib`), nunca en texto plano.
- ✅ JWT de acceso de vida corta (30 min) + refresh (7 días).
- ✅ El access token incluye los roles como claim, pero **cada endpoint
  vuelve a consultar los roles reales del usuario en BD** (`get_current_user`
  hace `selectinload(User.roles)`) — un usuario desactivado o con roles
  cambiados después de emitido el token pierde el acceso de inmediato en la
  siguiente request, no solo cuando expira el token.
- ✅ **Rate limiting real implementado en Fase 16** (antes solo estaba
  prometido en `docs/risks-security-scalability.md`): `/auth/login` bloquea
  tras 5 intentos fallidos por email en 60s y 30 por IP en 60s. Diseño
  importante: **solo los intentos fallidos cuentan** — un usuario legítimo
  logueándose muchas veces seguidas nunca se autobloquea.
- ⚠️ Refresh token sigue siendo stateless (sin tabla de revocación) — ya
  documentado como simplificación consciente desde Fase 3. Sigue siendo la
  recomendación pendiente si se necesita "cerrar sesión en todos los
  dispositivos".

## 2. Autorización (RBAC)

- ✅ Todo filtro de autorización vive en la capa de repositorio, nunca solo
  en el router — revisado en clientes (Fase 4), despachos (Fase 6/12), rutas
  (Fase 7), reportes (Fase 15), auditoría (Fase 16).
- ✅ CHOFER solo ve/actúa sobre sus propios despachos asignados (corregido en
  Fase 12, ver ese reporte de fase).
- ✅ CLIENTE solo ve sus propios registros vía `Customer.user_id`.
- ✅ El portal público de tracking (`/public/tracking/{code}`) nunca expone
  IDs internos — verificado con test explícito en Fase 13.
- ✅ Endpoints de gestión (crear chofer/vehículo/bodega) restringidos a
  ADMINISTRADOR; asignación de rutas a ADMINISTRADOR/DESPACHADOR; reportes y
  auditoría a ADMINISTRADOR/DESPACHADOR y solo ADMINISTRADOR respectivamente.

## 3. Endpoints

- ✅ CORS restringido a `settings.cors_origins` (por defecto solo
  `localhost:5173`) — ajustar en producción a los dominios reales.
- ✅ Subida de archivos (`/deliveries/evidence`) valida extensión permitida y
  tamaño máximo (8 MB) — ver Fase 12.
- ✅ Respuestas de error consistentes (`{"success": false, "error": {...}}`)
  en toda la API — sección 50 del prompt.
- ⚠️ HTTPS: no aplica en este entorno de desarrollo; queda para Fase 18
  (Nginx + Let's Encrypt), ya anotado en `docs/architecture.md`.

## 4. Datos

- ✅ Índice único parcial evita dos direcciones principales por cliente.
- ✅ `tracking_code` es UUID v4 no adivinable (protección del portal público).
- ✅ Contraseñas nunca se devuelven en ninguna respuesta de la API (schemas
  de salida no incluyen `password_hash`).
- ⚠️ Sin cifrado en reposo explícito más allá de lo que ofrezca la
  infraestructura de base de datos (RDS/Cloud SQL en producción); no se
  implementó cifrado a nivel de columna, se consideró fuera de alcance para
  este proyecto salvo que se requiera explícitamente.

## 5. Logs y auditoría

- ✅ **`audit_logs` implementado y poblado en Fase 16** (existía como tabla
  desde Fase 2 pero no se escribía en ningún endpoint). Se audita: creación
  de choferes (acción privilegiada — otorga acceso a un usuario nuevo) y toda
  transición de estado de despacho (usuario, IP, valor anterior/nuevo).
- ⚠️ **Cobertura parcial, no exhaustiva** — por alcance de tiempo, no se
  auditó: creación/edición de clientes, creación de vehículos/bodegas,
  actualización de despachos, reordenamiento de rutas. El servicio
  `AuditService` ya existe y es trivial extenderlo a estos puntos si se
  necesita trazabilidad completa; lo dejo señalado explícitamente en vez de
  darlo por hecho.
- ✅ Endpoint `GET /audit-logs` (solo ADMINISTRADOR) para revisión.

## 6. Hallazgos corregidos durante esta fase

1. `NotificationService.notify_user` solo hacía `flush()`, nunca `commit()`
   — las notificaciones se perdían silenciosamente (encontrado y corregido en
   Fase 14, no en esta, pero es un hallazgo de la clase "integridad de datos"
   relevante para esta auditoría).
2. Diseño inicial de rate limiting contaba también los intentos exitosos,
   lo que habría bloqueado a un usuario legítimo logueándose varias veces
   seguidas — rediseñado para contar solo fallos y resetear en éxito.

## 7. Pendientes explícitos para fases futuras

- Extender `AuditService` a más endpoints si se requiere trazabilidad
  completa (actualmente cubre las dos acciones más sensibles: alta de
  choferes y transiciones de estado).
- Revocación de refresh tokens (tabla de estado) si se necesita logout real.
- HTTPS/Nginx en Fase 18.
- Cifrado en reposo si lo exige algún requisito de cumplimiento no
  especificado en el prompt original.
