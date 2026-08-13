import uuid

from sqlalchemy.orm import Query, Session, selectinload

from app.models.customer import Customer, CustomerAddress
from app.models.user import User


def _scope_by_role(query: Query, current_user: User) -> Query:
    """Filtro de autorización aplicado SIEMPRE aquí, no en el router ni confiando en
    el frontend (ver docs/rbac.md, reglas 1 y 2)."""
    role_names = {r.name for r in current_user.roles}

    if "ADMINISTRADOR" in role_names or "DESPACHADOR" in role_names:
        return query  # ven todos los clientes

    if "VENDEDOR" in role_names:
        return query.filter(Customer.seller_id == current_user.id)

    if "CLIENTE" in role_names:
        # El usuario CLIENTE solo ve el/los registros Customer vinculados a su user_id
        return query.filter(Customer.user_id == current_user.id)

    # CHOFER u otro rol sin acceso a este recurso: no ve ningún cliente
    return query.filter(False)


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, current_user: User, skip: int = 0, limit: int = 50) -> list[Customer]:
        query = self.db.query(Customer).options(selectinload(Customer.addresses))
        query = _scope_by_role(query, current_user)
        return query.order_by(Customer.business_name).offset(skip).limit(limit).all()

    def get_for_user(self, customer_id: uuid.UUID, current_user: User) -> Customer | None:
        query = self.db.query(Customer).options(selectinload(Customer.addresses)).filter(
            Customer.id == customer_id
        )
        query = _scope_by_role(query, current_user)
        return query.first()

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.flush()
        return customer

    def update(self, customer: Customer, **fields) -> Customer:
        for key, value in fields.items():
            if value is not None:
                setattr(customer, key, value)
        self.db.flush()
        return customer


class CustomerAddressRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_customer(self, customer_id: uuid.UUID) -> list[CustomerAddress]:
        return (
            self.db.query(CustomerAddress)
            .filter(CustomerAddress.customer_id == customer_id)
            .order_by(CustomerAddress.es_principal.desc(), CustomerAddress.nombre)
            .all()
        )

    def get(self, address_id: uuid.UUID, customer_id: uuid.UUID) -> CustomerAddress | None:
        return (
            self.db.query(CustomerAddress)
            .filter(CustomerAddress.id == address_id, CustomerAddress.customer_id == customer_id)
            .first()
        )

    def create(self, address: CustomerAddress) -> CustomerAddress:
        self.db.add(address)
        self.db.flush()
        return address

    def unset_principal(self, customer_id: uuid.UUID, exclude_id: uuid.UUID | None = None) -> None:
        query = self.db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == customer_id, CustomerAddress.es_principal.is_(True)
        )
        if exclude_id:
            query = query.filter(CustomerAddress.id != exclude_id)
        query.update({"es_principal": False})
        self.db.flush()
