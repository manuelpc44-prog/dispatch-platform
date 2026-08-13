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
def despachador_token():
    return login("despachador@dispatchplatform.cl")


@pytest.fixture
def vendedor_token():
    return login("vendedor@dispatchplatform.cl")


def _make_ready_shipment(vendedor_token, despachador_token) -> str:
    """Crea un despacho y lo lleva a estado LISTO, listo para ser asignado."""
    customer_resp = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Cliente Ruta Test {uuid.uuid4().hex[:6]}",
            "address": {
                "nombre": "Principal", "calle": "Calle Test", "comuna": "Melipilla",
                "ciudad": "Melipilla", "region": "Metropolitana", "latitud": -33.5, "longitud": -70.6,
                "es_principal": True,
            },
        },
    ).json()
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]

    shipment = client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer_resp["id"],
            "address_id": customer_resp["addresses"][0]["id"],
            "warehouse_id": warehouse_id,
            "fecha_programada": "2026-09-10",
        },
    ).json()
    shipment_id = shipment["id"]
    client.post(
        f"/api/shipments/{shipment_id}/status",
        headers=auth_headers(despachador_token),
        json={"nuevo_estado": "PREPARANDO"},
    )
    client.post(
        f"/api/shipments/{shipment_id}/status",
        headers=auth_headers(despachador_token),
        json={"nuevo_estado": "LISTO"},
    )
    return shipment_id, warehouse_id


def _get_driver_and_vehicle(despachador_token) -> tuple[str, str]:
    driver_id = client.get("/api/drivers", headers=auth_headers(despachador_token)).json()[0]["id"]
    vehicle_id = client.get("/api/vehicles", headers=auth_headers(despachador_token)).json()[0]["id"]
    return driver_id, vehicle_id


def test_crear_ruta_con_multiples_despachos_los_pasa_a_asignado(despachador_token, vendedor_token):
    ids_and_wh = [_make_ready_shipment(vendedor_token, despachador_token) for _ in range(3)]
    shipment_ids = [x[0] for x in ids_and_wh]
    warehouse_id = ids_and_wh[0][1]
    driver_id, vehicle_id = _get_driver_and_vehicle(despachador_token)

    resp = client.post(
        "/api/routes",
        headers=auth_headers(despachador_token),
        json={
            "driver_id": driver_id, "vehicle_id": vehicle_id, "warehouse_id": warehouse_id,
            "fecha": "2026-09-10", "shipment_ids": shipment_ids,
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["estado"] == "ASIGNADA"
    assert len(data["stops"]) == 3
    assert [s["orden"] for s in data["stops"]] == [1, 2, 3]

    for sid in shipment_ids:
        shipment = client.get(f"/api/shipments/{sid}", headers=auth_headers(despachador_token)).json()
        assert shipment["estado"] == "ASIGNADO"
        assert shipment["driver_id"] == driver_id
        assert shipment["vehicle_id"] == vehicle_id


def test_no_se_puede_asignar_despacho_que_no_esta_listo(despachador_token, vendedor_token):
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    customer_resp = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={"business_name": f"Cliente No Listo {uuid.uuid4().hex[:6]}"},
    ).json()
    client.post(
        f"/api/customers/{customer_resp['id']}/addresses",
        headers=auth_headers(vendedor_token),
        json={
            "nombre": "P", "calle": "C", "comuna": "X", "ciudad": "X", "region": "X",
            "latitud": -33.0, "longitud": -70.0, "es_principal": True,
        },
    )
    customer_resp = client.get(
        f"/api/customers/{customer_resp['id']}", headers=auth_headers(vendedor_token)
    ).json()
    shipment = client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer_resp["id"], "address_id": customer_resp["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-09-10",
        },
    ).json()
    # Queda en PENDIENTE, no LISTO
    driver_id, vehicle_id = _get_driver_and_vehicle(despachador_token)

    resp = client.post(
        "/api/routes",
        headers=auth_headers(despachador_token),
        json={
            "driver_id": driver_id, "vehicle_id": vehicle_id, "warehouse_id": warehouse_id,
            "fecha": "2026-09-10", "shipment_ids": [shipment["id"]],
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "INVALID_ROUTE_ASSIGNMENT"


def test_reordenar_paradas_de_una_ruta(despachador_token, vendedor_token):
    ids_and_wh = [_make_ready_shipment(vendedor_token, despachador_token) for _ in range(2)]
    shipment_ids = [x[0] for x in ids_and_wh]
    warehouse_id = ids_and_wh[0][1]
    driver_id, vehicle_id = _get_driver_and_vehicle(despachador_token)

    route = client.post(
        "/api/routes",
        headers=auth_headers(despachador_token),
        json={
            "driver_id": driver_id, "vehicle_id": vehicle_id, "warehouse_id": warehouse_id,
            "fecha": "2026-09-10", "shipment_ids": shipment_ids,
        },
    ).json()
    route_id = route["id"]
    stops = route["stops"]

    reorder_resp = client.patch(
        f"/api/routes/{route_id}/stops/reorder",
        headers=auth_headers(despachador_token),
        json={"stops": [
            {"stop_id": stops[0]["id"], "orden": 2},
            {"stop_id": stops[1]["id"], "orden": 1},
        ]},
    )
    assert reorder_resp.status_code == 200
    new_stops = reorder_resp.json()["stops"]
    assert new_stops[0]["id"] == stops[1]["id"]
    assert new_stops[0]["orden"] == 1
    assert new_stops[1]["id"] == stops[0]["id"]
    assert new_stops[1]["orden"] == 2


def test_vendedor_no_puede_crear_ruta(despachador_token, vendedor_token):
    shipment_id, warehouse_id = _make_ready_shipment(vendedor_token, despachador_token)
    driver_id, vehicle_id = _get_driver_and_vehicle(despachador_token)
    resp = client.post(
        "/api/routes",
        headers=auth_headers(vendedor_token),
        json={
            "driver_id": driver_id, "vehicle_id": vehicle_id, "warehouse_id": warehouse_id,
            "fecha": "2026-09-10", "shipment_ids": [shipment_id],
        },
    )
    assert resp.status_code == 403


def test_ruta_sin_despachos_es_rechazada_por_validacion(despachador_token):
    driver_id, vehicle_id = _get_driver_and_vehicle(despachador_token)
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    resp = client.post(
        "/api/routes",
        headers=auth_headers(despachador_token),
        json={
            "driver_id": driver_id, "vehicle_id": vehicle_id, "warehouse_id": warehouse_id,
            "fecha": "2026-09-10", "shipment_ids": [],
        },
    )
    assert resp.status_code == 422  # violación de min_length=1 en Pydantic
