import uuid

from sqlalchemy.orm import Query, Session, selectinload

from app.models.customer import Customer
from app.models.shipment import Shipment, ShipmentStatusHistory
from app.models.user import User


def _scope_by_role(query: Query, current_user: User) -> Query:
    """Filtro de autorización aplicado en el repositorio (ver docs/rbac.md)."""
    role_names = {r.name for r in current_user.roles}

    if "ADMINISTRADOR" in role_names or "DESPACHADOR" in role_names:
        return query

    if "VENDEDOR" in role_names:
        return query.filter(Shipment.seller_id == current_user.id)

    if "CHOFER" in role_names:
        # El chofer ve los despachos donde driver_id apunta a SU perfil Driver
        # (asignado en Fase 7 vía Route). Implementado ahora en Fase 12, porque
        # es el primer punto donde el chofer necesita actuar sobre sus propios
        # despachos (registrar entregas/incidencias).
        from app.models.fleet import Driver
        from sqlalchemy import select

        driver_subq = select(Driver.id).where(Driver.user_id == current_user.id)
        return query.filter(Shipment.driver_id.in_(driver_subq))

    if "CLIENTE" in role_names:
        return query.join(Customer, Shipment.customer_id == Customer.id).filter(
            Customer.user_id == current_user.id
        )

    return query.filter(False)


class ShipmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, current_user: User, skip: int = 0, limit: int = 50) -> list[Shipment]:
        query = self.db.query(Shipment).options(selectinload(Shipment.items))
        query = _scope_by_role(query, current_user)
        return query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()

    def get_for_user(self, shipment_id: uuid.UUID, current_user: User) -> Shipment | None:
        query = self.db.query(Shipment).options(selectinload(Shipment.items)).filter(
            Shipment.id == shipment_id
        )
        query = _scope_by_role(query, current_user)
        return query.first()

    def get_by_tracking_code(self, tracking_code: uuid.UUID) -> Shipment | None:
        # Uso del portal público de cliente (Fase 13) — sin scope de rol, el UUID
        # no adivinable es la propia protección (ver docs/rbac.md regla 4).
        return (
            self.db.query(Shipment)
            .options(selectinload(Shipment.items))
            .filter(Shipment.tracking_code == tracking_code)
            .first()
        )

    def next_numero(self, year: int) -> str:
        prefix = f"DES-{year}-"
        last = (
            self.db.query(Shipment.numero)
            .filter(Shipment.numero.like(f"{prefix}%"))
            .order_by(Shipment.numero.desc())
            .first()
        )
        if last is None:
            seq = 1
        else:
            seq = int(last[0].split("-")[-1]) + 1
        return f"{prefix}{seq:06d}"

    def create(self, shipment: Shipment) -> Shipment:
        self.db.add(shipment)
        self.db.flush()
        return shipment

    def add_history_entry(self, entry: ShipmentStatusHistory) -> ShipmentStatusHistory:
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_history(self, shipment_id: uuid.UUID) -> list[ShipmentStatusHistory]:
        return (
            self.db.query(ShipmentStatusHistory)
            .filter(ShipmentStatusHistory.shipment_id == shipment_id)
            .order_by(ShipmentStatusHistory.created_at)
            .all()
        )
