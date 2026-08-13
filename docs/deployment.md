# Despliegue en Producción (Fase 18)

## Requisitos previos

- Un servidor Ubuntu/Debian con Docker y Docker Compose instalados.
- Un dominio apuntando (registro A) a la IP pública de ese servidor.
- Puertos 80 y 443 abiertos en el firewall.

## Pasos

### 1. Clonar el repositorio y configurar

```bash
git clone <tu-repositorio> dispatch-platform
cd dispatch-platform
cp .env.example .env
```

Edita `.env` con valores reales:
- `POSTGRES_PASSWORD`, `JWT_SECRET` — genera valores aleatorios largos
  (ej. `openssl rand -hex 32`)
- `CORS_ORIGINS` — tu dominio real, ej. `https://despacho.tuempresa.cl`
- `DOMAIN` — tu dominio, ej. `despacho.tuempresa.cl` (usado por Nginx)
- `FCM_CREDENTIALS` — si vas a usar notificaciones push (ver Fase 14 y
  `app/services/push_service.py` para las instrucciones completas)
- `MAPS_API_KEY`, `OSRM_URL` — si conectas un proveedor real de mapas/rutas
  (ver Fase 0 sobre la capa de abstracción)

### 2. Levantar la base de datos y aplicar migraciones

```bash
docker compose up -d postgres redis
docker compose run --rm backend alembic upgrade head
```

### 3. Emitir el certificado SSL (primera vez)

```bash
# Levanta Nginx solo en HTTP primero (comenta el bloque 443 temporalmente,
# o usa el modo standalone de certbot si el puerto 80 está libre)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot -w /var/www/certbot -d $DOMAIN --email tu-correo@ejemplo.cl --agree-tos
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### 4. Levantar todo

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Verifica: `curl https://$DOMAIN/api/health` debe devolver
`{"status":"ok",...}`.

### 5. Renovación automática del certificado

Agrega a un cron del host (los certificados de Let's Encrypt duran 90 días):

```cron
0 3 * * 1 cd /ruta/a/dispatch-platform && docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot renew && docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

## Verificación de la Prueba de Aceptación Final (sección 61 del prompt)

Con el sistema desplegado, sigue el flujo completo de la sección 61: admin
crea chofer/vehículo/cliente/direcciones → vendedor crea despacho →
despachador asigna → chofer inicia jornada desde la app Android → GPS
comienza → despachador ve el vehículo en el mapa en vivo → cliente ve su
seguimiento → chofer entrega los despachos uno a uno → regreso a bodega →
finalizar jornada → cliente ve COMPLETADO.

**Nota importante:** esta prueba de aceptación **no pudo ejecutarse de
extremo a extremo con la app Android real** en el entorno donde se
construyó este proyecto, porque Flutter no pudo compilarse aquí (ver
`mobile/driver_app/README.md`). El resto del flujo (backend, panel
despachador, portal cliente) sí fue probado de extremo a extremo en cada
fase. Antes de considerar el proyecto completo, corre esta prueba con la
app Android compilada en un entorno real.

## Monitoreo básico

- Logs: `docker compose logs -f backend` / `celery_worker` / `nginx`
- Salud: `GET /api/health` (verifica Postgres y Redis)
- Métricas más avanzadas (Prometheus/Grafana) quedan fuera del alcance de
  este prompt — se puede agregar `prometheus-fastapi-instrumentator` al
  backend si se necesita en el futuro.

## Rollback

Cada migración de Alembic tiene su `downgrade()` probado (ver reportes de
Fase 2 y 7). Para revertir una migración: `docker compose run --rm backend
alembic downgrade -1`. Para restaurar desde un backup completo, ver
`docs/backup.md`.
