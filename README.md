# Plataforma de Despachos, Rutas y GPS en Tiempo Real

Estado actual: **Fase 1 — Infraestructura** completada y probada.

## Arquitectura

Ver `docs/architecture.md`, `docs/database.md`, `docs/gps.md`, `docs/states.md` para el
diseño completo (Fase 0).

## Requisitos

- Docker y Docker Compose
- (Para desarrollo sin Docker): Python 3.12+, Node.js 22+, PostgreSQL 16, Redis 7

## Instalación con Docker

```bash
cp .env.example .env
# editar .env con valores reales, especialmente JWT_SECRET y contraseñas
docker compose up -d
```

- Backend: http://localhost:8000 (docs interactivos en `/docs`)
- Frontend: http://localhost:5173

## Verificación

```bash
curl http://localhost:8000/api/health
```

Debe responder `{"status":"ok","checks":{"api":"ok","database":"ok","redis":"ok"}}`.

## Desarrollo sin Docker (backend)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example ../.env  # o crear backend/.env con DATABASE_URL/REDIS_URL apuntando a tu Postgres/Redis local
uvicorn app.main:app --reload
```

## Desarrollo sin Docker (frontend)

```bash
cd frontend
npm install
npm run dev
```

## Estructura del proyecto

Ver `docs/structure.md`.

## Plan de fases

Ver `docs/roadmap.md`. El proyecto avanza fase por fase; cada fase se prueba antes de
avanzar a la siguiente.

## Producción

Ver `docs/deployment.md` para el despliegue completo (Docker + Nginx + HTTPS vía
Let's Encrypt) y `docs/backup.md` para backups. Resumen rápido:

```bash
cp .env.example .env   # completar con valores reales de producción
docker compose up -d postgres redis
docker compose run --rm backend alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

