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
def despachador_token():
    return login("despachador@dispatchplatform.cl")


def _create_shipment(vendedor_token, despachador_token):
    customer = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Cliente Tracking {uuid.uuid4().hex[:6]}",
            "address": {
                "nombre": "P", "calle": "C", "comuna": "Melipilla", "ciudad": "Melipilla",
                "region": "Metropolitana", "latitud": -33.5, "longitud": -70.6, "es_principal": True,
            },
        },
    ).json()
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    shipment = client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer["id"], "address_id": customer["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-12",
        },
    ).json()
    return shipment


def test_tracking_publico_no_requiere_autenticacion(vendedor_token, despachador_token):
    shipment = _create_shipment(vendedor_token, despachador_token)
    # Sin header Authorization
    resp = client.get(f"/api/public/tracking/{shipment['tracking_code']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["numero"] == shipment["numero"]
    assert data["destino_comuna"] == "Melipilla"


def test_tracking_publico_incluye_timeline(vendedor_token, despachador_token):
    shipment = _create_shipment(vendedor_token, despachador_token)
    client.post(
        f"/api/shipments/{shipment['id']}/status",
        headers=auth_headers(despachador_token),
        json={"nuevo_estado": "PREPARANDO"},
    )
    resp = client.get(f"/api/public/tracking/{shipment['tracking_code']}")
    timeline = resp.json()["timeline"]
    assert len(timeline) == 2
    assert timeline[0]["estado"] == "PENDIENTE"
    assert timeline[1]["estado"] == "PREPARANDO"


def test_tracking_code_inexistente_devuelve_404_sin_filtrar_info():
    resp = client.get(f"/api/public/tracking/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_tracking_publico_no_expone_ids_internos(vendedor_token, despachador_token):
    shipment = _create_shipment(vendedor_token, despachador_token)
    resp = client.get(f"/api/public/tracking/{shipment['tracking_code']}").json()
    # No debe filtrar customer_id, address_id, warehouse_id, driver_id, etc.
    forbidden_keys = {"id", "customer_id", "address_id", "warehouse_id", "driver_id", "vehicle_id", "seller_id"}
    assert forbidden_keys.isdisjoint(resp.keys())


def test_websocket_tracking_publico_sigue_funcionando(vendedor_token, despachador_token):
    """Regresión: confirma que el canal WS público de Fase 8 sigue vivo tras
    agregar el endpoint HTTP público de esta fase."""
    shipment = _create_shipment(vendedor_token, despachador_token)
    with client.websocket_connect(f"/ws/tracking/{shipment['tracking_code']}") as ws:
        assert ws is not None
