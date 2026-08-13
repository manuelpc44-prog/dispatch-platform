import datetime
import uuid

from fastapi import status
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, Forbidden
from app.models.customer import Customer, CustomerAddress
from app.models.enums import VALID_TRANSITIONS, ShipmentStatus
from app.models.fleet import Warehouse
from app.models.shipment import Shipment, ShipmentItem, ShipmentStatusHistory
from app.models.user import User
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.shipment import ShipmentCreate, ShipmentTransitionRequest, ShipmentUpdate


class ShipmentNotFound(DomainError):
    def __init__(self):
        super().__init__("SHIPMENT_NOT_FOUND", "Despacho no encontrado", status.HTTP_404_NOT_FOUND)


class InvalidReference(DomainError):
    def __init__(self, message: str):
        super().__init__("INVALID_REFERENCE", message, status.HTTP_400_BAD_REQUEST)


class InvalidTransition(DomainError):
    def __init__(self, desde: ShipmentStatus, hacia: ShipmentStatus):
        super().__init__(
            code="INVALID_TRANSITION",
            message=f"No se puede pasar de {desde.value} a {hacia.value}",
            status_code=status.HTTP_409_CONFLICT,
        )


class ShipmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ShipmentRepository(db)

    def _assert_can_create(self, current_user: User) -> None:
        role_names = {r.name for r in current_user.roles}
        if not role_names.intersection({"ADMINISTRADOR", "DESPACHADOR", "VENDEDOR"}):
            raise Forbidden("Solo ADMINISTRADOR, DESPACHADOR o VENDEDOR pueden crear despachos")

    def list_shipments(self, current_user: User, skip: int = 0, limit: int = 50) -> list[Shipment]:
        return self.repo.list_for_user(current_user, skip=skip, limit=limit)

    def get_shipment(self, shipment_id: uuid.UUID, current_user: User) -> Shipment:
        shipment = self.repo.get_for_user(shipment_id, current_user)
        if shipment is None:
            raise ShipmentNotFound()
        return shipment

    def get_by_tracking_code(self, tracking_code: uuid.UUID) -> Shipment:
        shipment = self.repo.get_by_tracking_code(tracking_code)
        if shipment is None:
            raise ShipmentNotFound()
        return shipment

    def get_public_tracking(self, tracking_code: uuid.UUID):
        """Vista pública y acotada — ver docs/rbac.md regla 4. Nunca expone
        IDs internos ni datos de otros despachos/clientes."""
        import json

        import redis as redis_lib

        from app.core.config import settings
        from app.models.customer import Customer, CustomerAddress
        from app.schemas.tracking_public import TrackingLivePosition, TrackingPublicOut

        shipment = self.get_by_tracking_code(tracking_code)
        customer = self.db.query(Customer).filter(Customer.id == shipment.customer_id).first()
        address = self.db.query(CustomerAddress).filter(CustomerAddress.id == shipment.address_id).first()
        history = self.repo.list_history(shipment.id)

        live_position = None
        if shipment.driver_id:
            r = redis_lib.Redis.from_url(settings.redis_url)
            try:
                raw = r.get(f"live:driver:{shipment.driver_id}")
                if raw:
                    data = json.loads(raw)
                    live_position = TrackingLivePosition(
                        latitude=data["latitude"],
                        longitude=data["longitude"],
                        recorded_at=data["recorded_at"],
                    )
            finally:
                r.close()

        return TrackingPublicOut(
            numero=shipment.numero,
            estado=shipment.estado,
            destino_comuna=address.comuna if address else "",
            destino_ciudad=address.ciudad if address else "",
            fecha_programada=shipment.fecha_programada,
            cliente_nombre=customer.business_name if customer else "",
            timeline=[
                {"estado": h.estado_nuevo, "created_at": h.created_at} for h in history
            ],
            live_position=live_position,
        )

    def create_shipment(self, payload: ShipmentCreate, current_user: User) -> Shipment:
        self._assert_can_create(current_user)

        customer = self.db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if customer is None:
            raise InvalidReference("El cliente indicado no existe")

        address = (
            self.db.query(CustomerAddress)
            .filter(
                CustomerAddress.id == payload.address_id,
                CustomerAddress.customer_id == payload.customer_id,
            )
            .first()
        )
        if address is None:
            raise InvalidReference("La dirección indicada no pertenece a ese cliente")

        warehouse = self.db.query(Warehouse).filter(Warehouse.id == payload.warehouse_id).first()
        if warehouse is None:
            raise InvalidReference("La bodega indicada no existe")

        role_names = {r.name for r in current_user.roles}
        seller_id = customer.seller_id
        if "VENDEDOR" in role_names and "ADMINISTRADOR" not in role_names:
            seller_id = current_user.id

        numero = self.repo.next_numero(payload.fecha_programada.year)

        shipment = Shipment(
            numero=numero,
            tracking_code=uuid.uuid4(),
            customer_id=payload.customer_id,
            address_id=payload.address_id,
            seller_id=seller_id,
            warehouse_id=payload.warehouse_id,
            fecha_programada=payload.fecha_programada,
            hora_programada=payload.hora_programada,
            prioridad=payload.prioridad,
            observaciones=payload.observaciones,
            estado=ShipmentStatus.CREADO,
        )
        for item in payload.items:
            shipment.items.append(ShipmentItem(**item.model_dump()))

        self.repo.create(shipment)

        # Transición automática CREADO -> PENDIENTE, registrada en el historial
        self._record_transition(shipment, ShipmentStatus.CREADO, ShipmentStatus.PENDIENTE, current_user, None)
        shipment.estado = ShipmentStatus.PENDIENTE

        self.db.commit()
        self.db.refresh(shipment)

        self._notify_created(shipment)
        return shipment

    def _notify_created(self, shipment: Shipment) -> None:
        from app.models.customer import Customer
        from app.services.notification_service import NotificationService

        customer = self.db.query(Customer).filter(Customer.id == shipment.customer_id).first()
        if customer and customer.user_id:
            NotificationService(self.db).notify_user(
                customer.user_id,
                tipo="SHIPMENT_CREADO",
                titulo="Despacho creado",
                cuerpo=f"Se creó tu despacho {shipment.numero}, pronto será preparado.",
                data={"shipment_id": str(shipment.id), "tracking_code": str(shipment.tracking_code)},
            )

    def update_shipment(self, shipment_id: uuid.UUID, payload: ShipmentUpdate, current_user: User) -> Shipment:
        self._assert_can_create(current_user)
        shipment = self.get_shipment(shipment_id, current_user)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(shipment, key, value)
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def _record_transition(
        self,
        shipment: Shipment,
        estado_anterior: ShipmentStatus | None,
        estado_nuevo: ShipmentStatus,
        current_user: User,
        observacion: str | None,
        gps_lat: float | None = None,
        gps_lng: float | None = None,
    ) -> None:
        entry = ShipmentStatusHistory(
            shipment_id=shipment.id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            user_id=current_user.id,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            observacion=observacion,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        self.repo.add_history_entry(entry)

    def transition(
        self, shipment_id: uuid.UUID, payload: ShipmentTransitionRequest, current_user: User, ip: str | None = None
    ) -> Shipment:
        shipment = self.get_shipment(shipment_id, current_user)
        estado_actual = shipment.estado

        if payload.nuevo_estado not in VALID_TRANSITIONS.get(estado_actual, set()):
            raise InvalidTransition(estado_actual, payload.nuevo_estado)

        self._record_transition(
            shipment,
            estado_actual,
            payload.nuevo_estado,
            current_user,
            payload.observacion,
            payload.gps_lat,
            payload.gps_lng,
        )
        shipment.estado = payload.nuevo_estado
        self.db.commit()
        self.db.refresh(shipment)

        from app.services.audit_service import AuditService

        AuditService(self.db).log_action(
            user_id=current_user.id,
            ip=ip,
            accion="TRANSITION",
            modulo="shipments",
            registro_id=str(shipment.id),
            valor_anterior={"estado": estado_actual.value},
            valor_nuevo={"estado": payload.nuevo_estado.value},
        )

        self._notify_transition(shipment, payload.nuevo_estado)
        return shipment

    # Mapear estado -> (título, cuerpo) del mensaje al CLIENTE (sección 31 del prompt).
    # Solo se notifica si el estado nuevo está en este diccionario.
    _CLIENTE_NOTIFICATIONS = {
        ShipmentStatus.ASIGNADO: ("Despacho asignado", "Tu despacho {numero} fue asignado a un transportista."),
        ShipmentStatus.SALIDA_BODEGA: ("Despacho en camino", "Tu despacho {numero} salió de bodega."),
        ShipmentStatus.EN_RUTA: ("En ruta", "Tu despacho {numero} está en ruta hacia tu dirección."),
        ShipmentStatus.LLEGADA_CLIENTE: ("Por llegar", "El chofer está próximo a llegar con tu despacho {numero}."),
        ShipmentStatus.ENTREGADO: ("Entregado", "Tu despacho {numero} fue entregado. ¡Gracias por tu compra!"),
        ShipmentStatus.INCIDENCIA: ("Incidencia reportada", "Hubo un inconveniente con tu despacho {numero}."),
    }

    def _notify_transition(self, shipment: Shipment, nuevo_estado: ShipmentStatus) -> None:
        from app.models.customer import Customer
        from app.services.notification_service import NotificationService

        notif_service = NotificationService(self.db)

        # Notificar al cliente, si tiene usuario con login vinculado
        entry = self._CLIENTE_NOTIFICATIONS.get(nuevo_estado)
        if entry:
            customer = self.db.query(Customer).filter(Customer.id == shipment.customer_id).first()
            if customer and customer.user_id:
                titulo, cuerpo_template = entry
                notif_service.notify_user(
                    customer.user_id,
                    tipo=f"SHIPMENT_{nuevo_estado.value}",
                    titulo=titulo,
                    cuerpo=cuerpo_template.format(numero=shipment.numero),
                    data={"shipment_id": str(shipment.id), "tracking_code": str(shipment.tracking_code)},
                )

        # Notificar al despachador que asignó/gestiona el despacho, en los
        # eventos operativos relevantes (sección 31 del prompt)
        despachador_events = {
            ShipmentStatus.SALIDA_BODEGA,
            ShipmentStatus.ENTREGADO,
            ShipmentStatus.NO_ENTREGADO,
            ShipmentStatus.INCIDENCIA,
            ShipmentStatus.REGRESO_BODEGA,
            ShipmentStatus.LLEGADA_BODEGA,
        }
        if nuevo_estado in despachador_events:
            notif_service.notify_dispatchers(
                tipo=f"DISPATCHER_{nuevo_estado.value}",
                titulo=f"Despacho {shipment.numero}",
                cuerpo=f"Cambió a estado {nuevo_estado.value}",
                data={"shipment_id": str(shipment.id)},
            )

    def get_history(self, shipment_id: uuid.UUID, current_user: User) -> list[ShipmentStatusHistory]:
        self.get_shipment(shipment_id, current_user)  # valida acceso + existencia
        return self.repo.list_history(shipment_id)
