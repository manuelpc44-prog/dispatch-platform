import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

PASSWORD = "Password123!"


def login(client: TestClient, email: str) -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def despachador_token(client):
    return login(client, "despachador@dispatchplatform.cl")


@pytest.fixture
def admin_token(client):
    return login(client, "admin@dispatchplatform.cl")


@pytest.fixture
def vendedor_token(client):
    return login(client, "vendedor@dispatchplatform.cl")


def _fresh_driver_and_vehicle(client, admin_token):
    """Crea un chofer y vehículo nuevos y exclusivos para este test, para evitar
    colisiones con jornadas activas dejadas por otros tests/corridas."""
    email = f"chofer-gps-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    driver = client.post(
        "/api/drivers",
        headers=auth_headers(admin_token),
        json={
            "email": email, "full_name": "Chofer GPS Test", "password": PASSWORD,
            "license_number": f"LIC-{uuid.uuid4().hex[:6]}",
        },
    ).json()
    vehicle = client.post(
        "/api/vehicles",
        headers=auth_headers(admin_token),
        json={"plate": f"G{uuid.uuid4().hex[:5].upper()}"},
    ).json()
    driver_token = login(client, email)
    return driver, vehicle, driver_token


def test_chofer_inicia_jornada(client, admin_token):
    _, vehicle, driver_token = _fresh_driver_and_vehicle(client, admin_token)
    resp = client.post(
        "/api/shifts/start",
        headers=auth_headers(driver_token),
        json={"vehicle_id": vehicle["id"]},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["estado"] == "INICIADA"


def test_no_se_puede_iniciar_dos_jornadas_activas(client, admin_token):
    _, vehicle, driver_token = _fresh_driver_and_vehicle(client, admin_token)
    r1 = client.post("/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]})
    assert r1.status_code == 201
    r2 = client.post("/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]})
    assert r2.status_code == 409
    assert r2.json()["detail"]["error"]["code"] == "SHIFT_ALREADY_ACTIVE"


def test_no_se_puede_enviar_gps_sin_jornada_activa(client, admin_token):
    _, vehicle, driver_token = _fresh_driver_and_vehicle(client, admin_token)
    resp = client.post(
        "/api/tracking/location",
        headers=auth_headers(driver_token),
        json={"positions": [{
            "client_uuid": str(uuid.uuid4()), "latitude": -33.5, "longitude": -70.6,
            "recorded_at": "2026-08-08T10:00:00Z",
        }]},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "NO_ACTIVE_SHIFT"


def test_ingesta_gps_es_idempotente_por_client_uuid(client, admin_token):
    _, vehicle, driver_token = _fresh_driver_and_vehicle(client, admin_token)
    client.post("/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]})

    client_uuid = str(uuid.uuid4())
    payload = {"positions": [{
        "client_uuid": client_uuid, "latitude": -33.5, "longitude": -70.6,
        "recorded_at": "2026-08-08T10:00:00Z",
    }]}

    r1 = client.post("/api/tracking/location", headers=auth_headers(driver_token), json=payload)
    assert r1.status_code == 200
    assert r1.json() == {"received": 1, "inserted": 1, "duplicates": 0}

    r2 = client.post("/api/tracking/location", headers=auth_headers(driver_token), json=payload)
    assert r2.status_code == 200
    assert r2.json() == {"received": 1, "inserted": 0, "duplicates": 1}


def test_historial_de_posiciones_de_la_jornada(client, admin_token):
    _, vehicle, driver_token = _fresh_driver_and_vehicle(client, admin_token)
    shift = client.post(
        "/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]}
    ).json()

    for i in range(3):
        client.post(
            "/api/tracking/location",
            headers=auth_headers(driver_token),
            json={"positions": [{
                "client_uuid": str(uuid.uuid4()), "latitude": -33.5 - i * 0.001, "longitude": -70.6,
                "recorded_at": f"2026-08-08T10:0{i}:00Z",
            }]},
        )

    history = client.get(
        f"/api/shifts/{shift['id']}/positions", headers=auth_headers(driver_token)
    ).json()
    assert len(history) == 3


def test_finalizar_jornada(client, admin_token):
    _, vehicle, driver_token = _fresh_driver_and_vehicle(client, admin_token)
    shift = client.post(
        "/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]}
    ).json()

    resp = client.post(f"/api/shifts/{shift['id']}/end", headers=auth_headers(driver_token), json={})
    assert resp.status_code == 200
    assert resp.json()["estado"] == "FINALIZADA"

    # Tras finalizar, debe poder iniciar una jornada nueva sin conflicto
    r2 = client.post("/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]})
    assert r2.status_code == 201


def test_vendedor_no_puede_iniciar_jornada(client, vendedor_token, admin_token):
    _, vehicle, _ = _fresh_driver_and_vehicle(client, admin_token)
    resp = client.post(
        "/api/shifts/start", headers=auth_headers(vendedor_token), json={"vehicle_id": vehicle["id"]}
    )
    assert resp.status_code == 403


def test_websocket_dispatcher_recibe_posicion_en_tiempo_real(client, admin_token, despachador_token):
    _, vehicle, driver_token = _fresh_driver_and_vehicle(client, admin_token)
    client.post("/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]})

    with client.websocket_connect(f"/ws/dispatcher?token={despachador_token}") as ws:
        client.post(
            "/api/tracking/location",
            headers=auth_headers(driver_token),
            json={"positions": [{
                "client_uuid": str(uuid.uuid4()), "latitude": -33.55, "longitude": -70.65, "speed": 42,
                "recorded_at": "2026-08-08T11:00:00Z",
            }]},
        )
        message = ws.receive_json()
        assert message["latitude"] == -33.55
        assert message["speed"] == 42


def test_websocket_dispatcher_rechaza_token_invalido(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/dispatcher?token=token-invalido") as ws:
            ws.receive_json()


def test_websocket_tracking_publico_recibe_solo_su_despacho(client, admin_token, despachador_token, vendedor_token):
    driver, vehicle, driver_token = _fresh_driver_and_vehicle(client, admin_token)

    customer = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Cliente WS Test {uuid.uuid4().hex[:6]}",
            "address": {
                "nombre": "P", "calle": "C", "comuna": "X", "ciudad": "X", "region": "X",
                "latitud": -33.5, "longitud": -70.6, "es_principal": True,
            },
        },
    ).json()
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    shipment = client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer["id"], "address_id": customer["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-08",
        },
    ).json()
    client.post(f"/api/shipments/{shipment['id']}/status", headers=auth_headers(despachador_token), json={"nuevo_estado": "PREPARANDO"})
    client.post(f"/api/shipments/{shipment['id']}/status", headers=auth_headers(despachador_token), json={"nuevo_estado": "LISTO"})
    client.post(
        "/api/routes",
        headers=auth_headers(despachador_token),
        json={
            "driver_id": driver["id"], "vehicle_id": vehicle["id"], "warehouse_id": warehouse_id,
            "fecha": "2026-08-08", "shipment_ids": [shipment["id"]],
        },
    )
    client.post("/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"], "fecha": "2026-08-08"})

    tracking_code = shipment["tracking_code"]
    with client.websocket_connect(f"/ws/tracking/{tracking_code}") as ws:
        client.post(
            "/api/tracking/location",
            headers=auth_headers(driver_token),
            json={"positions": [{
                "client_uuid": str(uuid.uuid4()), "latitude": -33.60, "longitude": -70.70, "speed": 10,
                "recorded_at": "2026-08-08T11:05:00Z",
            }]},
        )
        message = ws.receive_json()
        assert message["latitude"] == -33.60
