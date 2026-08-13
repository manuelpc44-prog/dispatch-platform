import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PASSWORD = "Password123!"


def login(email: str) -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def vendedor_token():
    return login("vendedor@dispatchplatform.cl")


@pytest.fixture
def shipment_context(vendedor_token):
    """Crea un cliente con dirección y bodega listos para crear un despacho."""
    customer_resp = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Cliente Shipment Test {uuid.uuid4().hex[:6]}",
            "address": {
                "nombre": "Principal", "calle": "Calle Test", "comuna": "Melipilla",
                "ciudad": "Melipilla", "region": "Metropolitana", "latitud": -33.5, "longitud": -70.6,
                "es_principal": True,
            },
        },
    )
    customer = customer_resp.json()
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(vendedor_token)).json()[0]["id"]
    return {
        "customer_id": customer["id"],
        "address_id": customer["addresses"][0]["id"],
        "warehouse_id": warehouse_id,
    }


def test_crear_despacho_genera_numero_con_formato_correcto(vendedor_token, shipment_context):
    resp = client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={**shipment_context, "fecha_programada": "2026-09-01"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["numero"].startswith("DES-2026-")
    assert len(data["numero"].split("-")[-1]) == 6
    # Se transiciona automáticamente CREADO -> PENDIENTE
    assert data["estado"] == "PENDIENTE"


def test_numeros_de_despacho_son_secuenciales_y_unicos(vendedor_token, shipment_context):
    resp1 = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={**shipment_context, "fecha_programada": "2026-09-01"},
    )
    resp2 = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={**shipment_context, "fecha_programada": "2026-09-01"},
    )
    numero1 = resp1.json()["numero"]
    numero2 = resp2.json()["numero"]
    assert numero1 != numero2
    seq1 = int(numero1.split("-")[-1])
    seq2 = int(numero2.split("-")[-1])
    assert seq2 == seq1 + 1


def test_creacion_registra_transicion_en_historial(vendedor_token, shipment_context):
    resp = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={**shipment_context, "fecha_programada": "2026-09-01"},
    )
    shipment_id = resp.json()["id"]
    history = client.get(
        f"/api/shipments/{shipment_id}/history", headers=auth_headers(vendedor_token)
    ).json()
    assert len(history) == 1
    assert history[0]["estado_anterior"] == "CREADO"
    assert history[0]["estado_nuevo"] == "PENDIENTE"


def test_transicion_invalida_es_rechazada(vendedor_token, shipment_context):
    resp = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={**shipment_context, "fecha_programada": "2026-09-01"},
    )
    shipment_id = resp.json()["id"]

    invalid = client.post(
        f"/api/shipments/{shipment_id}/status",
        headers=auth_headers(vendedor_token),
        json={"nuevo_estado": "COMPLETADO"},
    )
    assert invalid.status_code == 409
    assert invalid.json()["detail"]["error"]["code"] == "INVALID_TRANSITION"


def test_transicion_valida_actualiza_estado_y_agrega_historial(vendedor_token, shipment_context):
    resp = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={**shipment_context, "fecha_programada": "2026-09-01"},
    )
    shipment_id = resp.json()["id"]

    valid = client.post(
        f"/api/shipments/{shipment_id}/status",
        headers=auth_headers(vendedor_token),
        json={"nuevo_estado": "PREPARANDO", "observacion": "test"},
    )
    assert valid.status_code == 200
    assert valid.json()["estado"] == "PREPARANDO"

    history = client.get(
        f"/api/shipments/{shipment_id}/history", headers=auth_headers(vendedor_token)
    ).json()
    assert len(history) == 2
    assert history[-1]["estado_nuevo"] == "PREPARANDO"


def test_estados_terminales_no_permiten_ninguna_transicion(vendedor_token, shipment_context):
    resp = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={**shipment_context, "fecha_programada": "2026-09-01"},
    )
    shipment_id = resp.json()["id"]

    # Llevar el despacho a CANCELADO (transición válida desde PENDIENTE)
    cancel = client.post(
        f"/api/shipments/{shipment_id}/status",
        headers=auth_headers(vendedor_token),
        json={"nuevo_estado": "CANCELADO"},
    )
    assert cancel.status_code == 200
    assert cancel.json()["estado"] == "CANCELADO"

    # Ningún estado siguiente debe ser válido
    retry = client.post(
        f"/api/shipments/{shipment_id}/status",
        headers=auth_headers(vendedor_token),
        json={"nuevo_estado": "PENDIENTE"},
    )
    assert retry.status_code == 409


def test_direccion_de_otro_cliente_es_rechazada(vendedor_token, shipment_context):
    otro_cliente = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Otro Cliente {uuid.uuid4().hex[:6]}",
            "address": {
                "nombre": "Principal", "calle": "X", "comuna": "X", "ciudad": "X",
                "region": "X", "latitud": -33.0, "longitud": -70.0, "es_principal": True,
            },
        },
    ).json()
    otra_direccion_id = otro_cliente["addresses"][0]["id"]

    resp = client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={
            "customer_id": shipment_context["customer_id"],  # cliente A
            "address_id": otra_direccion_id,  # dirección de cliente B
            "warehouse_id": shipment_context["warehouse_id"],
            "fecha_programada": "2026-09-01",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "INVALID_REFERENCE"


def test_chofer_no_puede_crear_despacho(shipment_context):
    chofer_token = login("chofer1@dispatchplatform.cl")
    resp = client.post(
        "/api/shipments", headers=auth_headers(chofer_token),
        json={**shipment_context, "fecha_programada": "2026-09-01"},
    )
    assert resp.status_code == 403
