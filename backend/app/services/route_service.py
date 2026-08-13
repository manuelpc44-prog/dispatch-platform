import uuid

from fastapi import status
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, Forbidden
from app.models.enums import ShipmentStatus
from app.models.fleet import Driver, Vehicle
from app.models.fleet import Warehouse
from app.models.route import Route, RouteStop
from app.models.shipment import Shipment
from app.models.user import User
from app.repositories.route_repository import RouteRepository
from app.schemas.route import RouteCreate, RouteStopsReorderRequest
from app.schemas.shipment import ShipmentTransitionRequest
from app.services.shipment_service import ShipmentService


class RouteNotFound(DomainError):
    def __init__(self):
        super().__init__("ROUTE_NOT_FOUND", "Ruta no encontrada", status.HTTP_404_NOT_FOUND)


class InvalidRouteAssignment(DomainError):
    def __init__(self, message: str):
        super().__init__("INVALID_ROUTE_ASSIGNMENT", message, status.HTTP_400_BAD_REQUEST)


class ShipmentAlreadyAssigned(DomainError):
    def __init__(self, numero: str):
        super().__init__(
            code="SHIPMENT_ALREADY_ASSIGNED",
            message=f"El despacho {numero} ya está asignado a otra ruta activa",
            status_code=status.HTTP_409_CONFLICT,
        )


def _assert_can_manage(current_user: User) -> None:
    role_names = {r.name for r in current_user.roles}
    if not role_names.intersection({"ADMINISTRADOR", "DESPACHADOR"}):
        raise Forbidden("Solo ADMINISTRADOR o DESPACHADOR pueden asignar rutas")


class RouteService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RouteRepository(db)
        self.shipment_service = ShipmentService(db)

    def list_routes(self, skip: int = 0, limit: int = 50) -> list[Route]:
        return self.repo.list(skip=skip, limit=limit)

    def get_route(self, route_id: uuid.UUID) -> Route:
        route = self.repo.get(route_id)
        if route is None:
            raise RouteNotFound()
        return route

    def create_route(self, payload: RouteCreate, current_user: User) -> Route:
        _assert_can_manage(current_user)

        driver = self.db.query(Driver).filter(Driver.id == payload.driver_id).first()
        if driver is None or not driver.active:
            raise InvalidRouteAssignment("El chofer indicado no existe o está inactivo")

        vehicle = self.db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
        if vehicle is None or not vehicle.active:
            raise InvalidRouteAssignment("El vehículo indicado no existe o está inactivo")

        warehouse = self.db.query(Warehouse).filter(Warehouse.id == payload.warehouse_id).first()
        if warehouse is None:
            raise InvalidRouteAssignment("La bodega indicada no existe")

        # No se establece un límite artificial de despachos por ruta (sección 16 del prompt)
        shipments: list[Shipment] = []
        for shipment_id in payload.shipment_ids:
            shipment = self.db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if shipment is None:
                raise InvalidRouteAssignment(f"El despacho {shipment_id} no existe")
            if shipment.estado != ShipmentStatus.LISTO:
                raise InvalidRouteAssignment(
                    f"El despacho {shipment.numero} debe estar en estado LISTO para asignarse "
                    f"(está en {shipment.estado.value})"
                )
            if self.repo.shipment_already_in_active_route(shipment.id):
                raise ShipmentAlreadyAssigned(shipment.numero)
            shipments.append(shipment)

        route = Route(
            driver_id=payload.driver_id,
            vehicle_id=payload.vehicle_id,
            warehouse_id=payload.warehouse_id,
            fecha=payload.fecha,
            estado="PLANIFICADA",
        )
        self.repo.create(route)

        for index, shipment in enumerate(shipments, start=1):
            stop = RouteStop(route_id=route.id, shipment_id=shipment.id, orden=index)
            self.db.add(stop)

            shipment.driver_id = payload.driver_id
            shipment.vehicle_id = payload.vehicle_id
            self.shipment_service.transition(
                shipment.id,
                ShipmentTransitionRequest(nuevo_estado=ShipmentStatus.ASIGNADO),
                current_user,
            )

        route.estado = "ASIGNADA"
        self.db.commit()
        self.db.refresh(route)
        return route

    def reorder_stops(
        self, route_id: uuid.UUID, payload: RouteStopsReorderRequest, current_user: User
    ) -> Route:
        _assert_can_manage(current_user)
        route = self.get_route(route_id)

        route_stop_ids = {stop.id for stop in route.stops}
        payload_ids = {item.stop_id for item in payload.stops}
        if route_stop_ids != payload_ids:
            raise InvalidRouteAssignment(
                "Debes incluir exactamente todas las paradas de la ruta al reordenar"
            )

        ordenes = [item.orden for item in payload.stops]
        if len(set(ordenes)) != len(ordenes):
            raise InvalidRouteAssignment("Los valores de 'orden' deben ser únicos")

        for item in payload.stops:
            stop = self.repo.get_stop(item.stop_id, route_id)
            stop.orden = item.orden

        self.db.commit()
        self.db.refresh(route)
        return route
