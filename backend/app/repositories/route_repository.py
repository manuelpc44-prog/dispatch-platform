import uuid

from sqlalchemy.orm import Query, Session, selectinload

from app.models.route import Route, RouteStop
from app.models.user import User


def _scope_by_role(query: Query, current_user: User):
    role_names = {r.name for r in current_user.roles}
    if "ADMINISTRADOR" in role_names or "DESPACHADOR" in role_names:
        return query
    # CHOFER ve sus propias rutas (por driver_id ligado a su user_id) — se resuelve
    # completamente en Fase 11 cuando exista el vínculo driver activo; por ahora el
    # filtro exacto vive en el service, que sí conoce el Driver del usuario.
    return query


class RouteRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, skip: int = 0, limit: int = 50) -> list[Route]:
        return (
            self.db.query(Route)
            .options(selectinload(Route.stops))
            .order_by(Route.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get(self, route_id: uuid.UUID) -> Route | None:
        return (
            self.db.query(Route)
            .options(selectinload(Route.stops))
            .filter(Route.id == route_id)
            .first()
        )

    def create(self, route: Route) -> Route:
        self.db.add(route)
        self.db.flush()
        return route

    def get_stop(self, stop_id: uuid.UUID, route_id: uuid.UUID) -> RouteStop | None:
        return (
            self.db.query(RouteStop)
            .filter(RouteStop.id == stop_id, RouteStop.route_id == route_id)
            .first()
        )

    def shipment_already_in_active_route(self, shipment_id: uuid.UUID) -> bool:
        return (
            self.db.query(RouteStop)
            .join(Route, RouteStop.route_id == Route.id)
            .filter(RouteStop.shipment_id == shipment_id, Route.estado != "CANCELADA")
            .first()
            is not None
        )
