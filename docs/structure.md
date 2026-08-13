# Estructura Definitiva del Proyecto

Se mantiene la estructura propuesta en el prompt maestro (sección 6), con dos añadidos:

- `backend/app/core/` incluye explícitamente `security.py` (JWT), `config.py` (Settings vía
  pydantic-settings) y `exceptions.py` (excepciones de dominio → mapeadas a respuestas HTTP
  consistentes, sección 50).
- `backend/app/websocket/` separado de `api/` porque el ciclo de vida de una conexión WS
  (accept, mantener viva, fan-out) es distinto al de un request/response REST.

```
dispatch-platform/
├── backend/
│   ├── app/
│   │   ├── api/            # routers HTTP (auth, customers, shipments, routes, tracking...)
│   │   ├── core/           # config, seguridad JWT, excepciones, settings
│   │   ├── db/              # engine, session, base declarativa
│   │   ├── models/          # entidades SQLAlchemy
│   │   ├── schemas/         # contratos Pydantic in/out
│   │   ├── services/        # lógica de negocio (máquina de estados, asignación, RBAC)
│   │   ├── repositories/    # acceso a datos, filtros de autorización por rol
│   │   ├── websocket/       # connection manager, canales por rol
│   │   ├── workers/         # tareas Celery (FCM, cálculo de rutas, limpieza)
│   │   └── main.py
│   ├── alembic/              # migraciones
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/{components,pages,layouts,hooks,services,stores,types,utils}/
│   ├── package.json
│   └── Dockerfile
├── mobile/driver_app/
│   ├── lib/{screens,services,models,providers,repositories,widgets}/
│   ├── android/
│   └── pubspec.yaml
├── nginx/
├── docker/
├── scripts/
├── docs/
│   ├── architecture.md, database.md, rbac.md, states.md, gps.md,
│   │   websocket.md (Fase 8), api.md (Fase 8+), android.md (Fase 10-11),
│   │   deployment.md (Fase 18), backup.md (Fase 18), security.md,
│   │   troubleshooting.md (según se acumulen incidentes reales)
├── tests/                    # tests de integración end-to-end
├── docker-compose.yml
├── .env.example
└── README.md
```

Ya creada como esqueleto de carpetas (sin código todavía, según regla de Fase 0).
