import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, Forbidden
from app.models.customer import Customer, CustomerAddress
from app.models.user import User
from app.repositories.customer_repository import CustomerAddressRepository, CustomerRepository
from app.schemas.customer import CustomerAddressCreate, CustomerAddressUpdate, CustomerCreate, CustomerUpdate
from app.services.geocoding import get_geocoding_provider
from fastapi import status


class CustomerNotFound(DomainError):
    def __init__(self):
        super().__init__(
            code="CUSTOMER_NOT_FOUND",
            message="Cliente no encontrado",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AddressNotFound(DomainError):
    def __init__(self):
        super().__init__(
            code="ADDRESS_NOT_FOUND",
            message="Dirección no encontrada",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.customers = CustomerRepository(db)
        self.addresses = CustomerAddressRepository(db)

    def _assert_can_manage(self, current_user: User) -> None:
        role_names = {r.name for r in current_user.roles}
        if not role_names.intersection({"ADMINISTRADOR", "VENDEDOR"}):
            raise Forbidden("Solo ADMINISTRADOR o VENDEDOR pueden crear/editar clientes")

    def list_customers(self, current_user: User, skip: int = 0, limit: int = 50) -> list[Customer]:
        return self.customers.list_for_user(current_user, skip=skip, limit=limit)

    def get_customer(self, customer_id: uuid.UUID, current_user: User) -> Customer:
        customer = self.customers.get_for_user(customer_id, current_user)
        if customer is None:
            raise CustomerNotFound()
        return customer

    def create_customer(self, payload: CustomerCreate, current_user: User) -> Customer:
        self._assert_can_manage(current_user)

        role_names = {r.name for r in current_user.roles}
        seller_id = payload.seller_id
        if "VENDEDOR" in role_names and "ADMINISTRADOR" not in role_names:
            seller_id = current_user.id  # un vendedor no puede asignar clientes a otro vendedor

        customer = Customer(
            business_name=payload.business_name,
            tax_id=payload.tax_id,
            phone=payload.phone,
            email=payload.email,
            seller_id=seller_id,
        )
        self.customers.create(customer)

        if payload.address:
            self._create_address(customer.id, payload.address)

        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update_customer(self, customer_id: uuid.UUID, payload: CustomerUpdate, current_user: User) -> Customer:
        self._assert_can_manage(current_user)
        customer = self.get_customer(customer_id, current_user)
        self.customers.update(customer, **payload.model_dump(exclude_unset=True))
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def list_addresses(self, customer_id: uuid.UUID, current_user: User) -> list[CustomerAddress]:
        self.get_customer(customer_id, current_user)  # valida acceso + existencia
        return self.addresses.list_for_customer(customer_id)

    def _create_address(self, customer_id: uuid.UUID, payload: CustomerAddressCreate) -> CustomerAddress:
        lat, lng = payload.latitud, payload.longitud
        if lat is None or lng is None:
            result = get_geocoding_provider().geocode(
                payload.calle, payload.numero, payload.comuna, payload.ciudad, payload.region
            )
            lat, lng = result.latitude, result.longitude

        if payload.es_principal:
            self.addresses.unset_principal(customer_id)

        address = CustomerAddress(
            customer_id=customer_id,
            nombre=payload.nombre,
            calle=payload.calle,
            numero=payload.numero,
            comuna=payload.comuna,
            ciudad=payload.ciudad,
            region=payload.region,
            codigo_postal=payload.codigo_postal,
            latitud=lat,
            longitud=lng,
            contacto=payload.contacto,
            telefono=payload.telefono,
            observaciones=payload.observaciones,
            es_principal=payload.es_principal,
            activa=payload.activa,
        )
        return self.addresses.create(address)

    def create_address(
        self, customer_id: uuid.UUID, payload: CustomerAddressCreate, current_user: User
    ) -> CustomerAddress:
        self._assert_can_manage(current_user)
        self.get_customer(customer_id, current_user)  # valida acceso + existencia
        address = self._create_address(customer_id, payload)
        self.db.commit()
        self.db.refresh(address)
        return address

    def update_address(
        self,
        customer_id: uuid.UUID,
        address_id: uuid.UUID,
        payload: CustomerAddressUpdate,
        current_user: User,
    ) -> CustomerAddress:
        self._assert_can_manage(current_user)
        self.get_customer(customer_id, current_user)  # valida acceso + existencia
        address = self.addresses.get(address_id, customer_id)
        if address is None:
            raise AddressNotFound()

        data = payload.model_dump(exclude_unset=True)
        if data.get("es_principal") is True:
            self.addresses.unset_principal(customer_id, exclude_id=address_id)

        for key, value in data.items():
            setattr(address, key, value)
        self.db.commit()
        self.db.refresh(address)
        return address
