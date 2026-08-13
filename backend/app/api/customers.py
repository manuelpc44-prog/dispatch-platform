import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer import (
    CustomerAddressCreate,
    CustomerAddressOut,
    CustomerAddressUpdate,
    CustomerCreate,
    CustomerUpdate,
    CustomerWithAddressesOut,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerWithAddressesOut])
def list_customers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CustomerWithAddressesOut]:
    service = CustomerService(db)
    return service.list_customers(current_user, skip=skip, limit=limit)


@router.post("", response_model=CustomerWithAddressesOut, status_code=201)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerWithAddressesOut:
    service = CustomerService(db)
    return service.create_customer(payload, current_user)


@router.get("/{customer_id}", response_model=CustomerWithAddressesOut)
def get_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerWithAddressesOut:
    service = CustomerService(db)
    return service.get_customer(customer_id, current_user)


@router.patch("/{customer_id}", response_model=CustomerWithAddressesOut)
def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerWithAddressesOut:
    service = CustomerService(db)
    return service.update_customer(customer_id, payload, current_user)


@router.get("/{customer_id}/addresses", response_model=list[CustomerAddressOut])
def list_addresses(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CustomerAddressOut]:
    service = CustomerService(db)
    return service.list_addresses(customer_id, current_user)


@router.post("/{customer_id}/addresses", response_model=CustomerAddressOut, status_code=201)
def create_address(
    customer_id: uuid.UUID,
    payload: CustomerAddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerAddressOut:
    service = CustomerService(db)
    return service.create_address(customer_id, payload, current_user)


@router.patch("/{customer_id}/addresses/{address_id}", response_model=CustomerAddressOut)
def update_address(
    customer_id: uuid.UUID,
    address_id: uuid.UUID,
    payload: CustomerAddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerAddressOut:
    service = CustomerService(db)
    return service.update_address(customer_id, address_id, payload, current_user)
