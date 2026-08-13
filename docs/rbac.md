# Modelo de Usuarios y Permisos (RBAC)

## Roles

```
ADMINISTRADOR
DESPACHADOR
VENDEDOR
CHOFER
CLIENTE
```

## Principio de diseño

RBAC de dos niveles: **rol** (grueso, define el menú/vista disponible) + **permiso granular**
(fino, valida cada acción en backend). Un usuario puede tener más de un rol, pero en la
práctica cada persona típicamente tiene uno.

`user_roles` es many-to-many para soportar casos futuros (ej. un despachador que también
vende), sin forzarlo desde el inicio.

## Matriz de permisos (resumen — ver `docs/api.md` para el detalle endpoint por endpoint)

| Recurso                  | ADMIN | DESPACHADOR | VENDEDOR | CHOFER | CLIENTE |
|---------------------------|:---:|:---:|:---:|:---:|:---:|
| Usuarios (crear/editar)   | ✅ | ❌ | ❌ | ❌ | ❌ |
| Vehículos/Bodegas (CRUD)  | ✅ | 👁 | 👁 | ❌ | ❌ |
| Clientes (crear/editar)   | ✅ | 👁 | ✅ | ❌ | 👁 propio |
| Direcciones               | ✅ | 👁 | ✅ | ❌ | 👁 propias |
| Despachos (crear)         | ✅ | ✅ | ✅ | ❌ | ❌ |
| Despachos (asignar)       | ✅ | ✅ | ❌ | ❌ | ❌ |
| Rutas (ver todas)         | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ruta propia (Android)     | — | — | — | ✅ | — |
| GPS en vivo (ver todos)   | ✅ | ✅ | ❌ | ❌ | ❌ |
| GPS en vivo (propio despacho) | — | — | — | — | ✅ |
| Enviar posición GPS       | ❌ | ❌ | ❌ | ✅ | ❌ |
| Entregas (registrar)      | ❌ | ❌ | ❌ | ✅ | ❌ |
| Incidencias (crear)       | ✅ | ✅ | ❌ | ✅ | ❌ |
| Auditoría                 | ✅ | ❌ | ❌ | ❌ | ❌ |
| Configuración sistema     | ✅ | ❌ | ❌ | ❌ | ❌ |

(👁 = solo lectura, alcance acotado)

## Reglas de autorización que van en backend, nunca solo en frontend

1. **CLIENTE**: todo repositorio que sirva datos de `customers`, `shipments`,
   `customer_addresses` inyecta `WHERE customer_id = current_user.customer_id`
   automáticamente cuando el rol activo es CLIENTE — no es un filtro opcional del query param.
2. **VENDEDOR**: puede ver únicamente despachos donde `seller_id = current_user.seller_id`.
3. **CHOFER**: la app Android solo puede leer/escribir sobre su `driver_shift_id` activa;
   el backend rechaza cualquier `shipment_id` que no pertenezca a una `route_stop` de esa
   jornada.
4. **Portal de tracking público** (`/seguimiento/{tracking_code}`) no requiere login, pero
   el `tracking_code` es un UUID no adivinable — el endpoint expone solo el despacho
   asociado a ese código, nunca una lista.
5. Dependencia FastAPI `get_current_user` + `require_role(...)` / `require_permission(...)`
   como decoradores/dependencias reutilizables en cada router — la validación de permiso vive
   una sola vez por endpoint, no duplicada en cada servicio.
