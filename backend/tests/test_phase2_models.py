import uuid

import pytest
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.enums import CANCELABLE_STATES, VALID_TRANSITIONS, ShipmentStatus


def test_all_states_have_transition_entry():
    for status in ShipmentStatus:
        assert status in VALID_TRANSITIONS, f"Falta {status} en VALID_TRANSITIONS"


def test_completado_y_cancelado_son_terminales():
    assert VALID_TRANSITIONS[ShipmentStatus.COMPLETADO] == set()
    assert VALID_TRANSITIONS[ShipmentStatus.CANCELADO] == set()


def test_no_se_puede_cancelar_despues_de_salir_de_bodega():
    post_salida = {
        ShipmentStatus.SALIDA_BODEGA,
        ShipmentStatus.EN_RUTA,
        ShipmentStatus.LLEGADA_CLIENTE,
        ShipmentStatus.ENTREGA_EN_PROCESO,
        ShipmentStatus.ENTREGADO,
        ShipmentStatus.NO_ENTREGADO,
        ShipmentStatus.INCIDENCIA,
        ShipmentStatus.REGRESO_BODEGA,
        ShipmentStatus.LLEGADA_BODEGA,
    }
    for status in post_salida:
        assert ShipmentStatus.CANCELADO not in VALID_TRANSITIONS[status]
        assert status not in CANCELABLE_STATES


def test_transicion_creado_a_completado_directo_es_invalida():
    assert ShipmentStatus.COMPLETADO not in VALID_TRANSITIONS[ShipmentStatus.CREADO]


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_conexion_real_a_postgres(db):
    result = db.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_indice_parcial_direccion_principal_existe(db):
    result = db.execute(
        text(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'customer_addresses' "
            "AND indexname = 'uq_customer_single_principal_address'"
        )
    ).fetchone()
    assert result is not None, "El índice único parcial no existe — revisar migraciones"


def test_no_se_permiten_dos_direcciones_principales_para_el_mismo_cliente(db):
    from sqlalchemy.exc import IntegrityError

    from app.models.customer import Customer, CustomerAddress

    customer = Customer(business_name=f"Test Corp {uuid.uuid4()}")
    db.add(customer)
    db.flush()

    addr1 = CustomerAddress(
        customer_id=customer.id, nombre="A", calle="Calle 1", comuna="X", ciudad="X",
        region="X", latitud=0, longitud=0, es_principal=True,
    )
    db.add(addr1)
    db.flush()

    addr2 = CustomerAddress(
        customer_id=customer.id, nombre="B", calle="Calle 2", comuna="X", ciudad="X",
        region="X", latitud=0, longitud=0, es_principal=True,
    )
    db.add(addr2)

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()


def test_numero_de_despacho_es_unico(db):
    from sqlalchemy.exc import IntegrityError

    from app.models.customer import Customer, CustomerAddress
    from app.models.fleet import Warehouse
    from app.models.shipment import Shipment
    import datetime

    customer = Customer(business_name=f"Dup Test {uuid.uuid4()}")
    db.add(customer)
    db.flush()
    addr = CustomerAddress(
        customer_id=customer.id, nombre="A", calle="Calle 1", comuna="X", ciudad="X",
        region="X", latitud=0, longitud=0, es_principal=True,
    )
    db.add(addr)
    warehouse = Warehouse(name=f"WH {uuid.uuid4()}", latitud=0, longitud=0)
    db.add(warehouse)
    db.flush()

    numero = f"DES-TEST-{uuid.uuid4().hex[:8]}"
    s1 = Shipment(
        numero=numero, tracking_code=uuid.uuid4(), customer_id=customer.id,
        address_id=addr.id, warehouse_id=warehouse.id, fecha_programada=datetime.date.today(),
    )
    db.add(s1)
    db.flush()

    s2 = Shipment(
        numero=numero, tracking_code=uuid.uuid4(), customer_id=customer.id,
        address_id=addr.id, warehouse_id=warehouse.id, fecha_programada=datetime.date.today(),
    )
    db.add(s2)
    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()
