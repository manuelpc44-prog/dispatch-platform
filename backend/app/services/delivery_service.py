import uuid

from fastapi import status
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, Forbidden
from app.models.delivery import Delivery, DeliveryEvidence
from app.models.enums import ShipmentStatus
from app.models.fleet import Driver
from app.models.misc import Incident
from app.models.user import User
from app.repositories.delivery_repository import DeliveryRepository, IncidentRepository
from app.schemas.delivery import DeliveryCreate, IncidentCreate
from app.schemas.shipment import ShipmentTransitionRequest
from app.services.shipment_service import ShipmentService


class DeliveryAlreadyExists(DomainError):
    def __init__(self):
        super().__init__(
            "DELIVERY_ALREADY_EXISTS",
            "Ya existe un registro de entrega para este despacho",
            status.HTTP_409_CONFLICT,
        )


class ShipmentNotInDeliveryState(DomainError):
    def __init__(self, estado_actual: str):
        super().__init__(
            code="SHIPMENT_NOT_IN_DELIVERY_STATE",
            message=f"El despacho debe estar en ENTREGA_EN_PROCESO para registrar la entrega "
            f"(está en {estado_actual})",
            status_code=status.HTTP_409_CONFLICT,
        )


def _assert_is_driver(db: Session, current_user: User) -> Driver:
    if "CHOFER" not in {r.name for r in current_user.roles}:
        raise Forbidden("Solo un chofer puede registrar entregas")
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if driver is None:
        raise Forbidden("El usuario actual no tiene un perfil de chofer asociado")
    return driver


class DeliveryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DeliveryRepository(db)
        self.shipment_service = ShipmentService(db)

    def create_delivery(self, payload: DeliveryCreate, current_user: User) -> Delivery:
        _assert_is_driver(self.db, current_user)

        if self.repo.get_by_shipment(payload.shipment_id) is not None:
            raise DeliveryAlreadyExists()

        shipment = self.shipment_service.get_shipment(payload.shipment_id, current_user)
        if shipment.estado != ShipmentStatus.ENTREGA_EN_PROCESO:
            raise ShipmentNotInDeliveryState(shipment.estado.value)

        delivery = Delivery(
            shipment_id=payload.shipment_id,
            receptor_nombre=payload.receptor_nombre,
            resultado=payload.resultado,
            motivo_fallo=payload.motivo_fallo,
            observacion=payload.observacion,
            gps_lat=payload.gps_lat,
            gps_lng=payload.gps_lng,
        )
        self.repo.create(delivery)

        for item in payload.evidence:
            self.repo.add_evidence(
                DeliveryEvidence(delivery_id=delivery.id, tipo=item.tipo, url=item.url)
            )

        nuevo_estado = (
            ShipmentStatus.ENTREGADO
            if payload.resultado.value == "ENTREGADO"
            else ShipmentStatus.NO_ENTREGADO
        )
        self.shipment_service.transition(
            payload.shipment_id,
            ShipmentTransitionRequest(
                nuevo_estado=nuevo_estado,
                observacion=payload.observacion,
                gps_lat=payload.gps_lat,
                gps_lng=payload.gps_lng,
            ),
            current_user,
        )

        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def get_by_shipment(self, shipment_id: uuid.UUID, current_user: User) -> Delivery | None:
        self.shipment_service.get_shipment(shipment_id, current_user)  # valida acceso
        return self.repo.get_by_shipment(shipment_id)


class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IncidentRepository(db)
        self.shipment_service = ShipmentService(db)

    def create_incident(self, payload: IncidentCreate, current_user: User) -> Incident:
        role_names = {r.name for r in current_user.roles}
        if not role_names.intersection({"ADMINISTRADOR", "DESPACHADOR", "CHOFER"}):
            raise Forbidden("No tienes permiso para reportar incidencias")

        shipment = self.shipment_service.get_shipment(payload.shipment_id, current_user)

        driver_id = None
        if "CHOFER" in role_names:
            driver = self.db.query(Driver).filter(Driver.user_id == current_user.id).first()
            driver_id = driver.id if driver else None

        incident = Incident(
            shipment_id=payload.shipment_id,
            driver_id=driver_id,
            tipo=payload.tipo,
            descripcion=payload.descripcion,
            gps_lat=payload.gps_lat,
            gps_lng=payload.gps_lng,
            resuelto=False,
        )
        self.repo.create(incident)

        # Transición a INCIDENCIA solo si el despacho está en un estado desde el
        # que esa transición es válida (ver VALID_TRANSITIONS) — si no, se registra
        # igual la incidencia pero sin forzar un cambio de estado inválido.
        from app.models.enums import VALID_TRANSITIONS

        if ShipmentStatus.INCIDENCIA in VALID_TRANSITIONS.get(shipment.estado, set()):
            self.shipment_service.transition(
                payload.shipment_id,
                ShipmentTransitionRequest(
                    nuevo_estado=ShipmentStatus.INCIDENCIA,
                    observacion=payload.descripcion,
                    gps_lat=payload.gps_lat,
                    gps_lng=payload.gps_lng,
                ),
                current_user,
            )

        self.db.commit()
        self.db.refresh(incident)
        return incident

    def list_for_shipment(self, shipment_id: uuid.UUID, current_user: User) -> list[Incident]:
        self.shipment_service.get_shipment(shipment_id, current_user)
        return self.repo.list_for_shipment(shipment_id)
