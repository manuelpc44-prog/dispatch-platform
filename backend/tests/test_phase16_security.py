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
def admin_token():
    return login("admin@dispatchplatform.cl")


@pytest.fixture
def despachador_token():
    return login("despachador@dispatchplatform.cl")


def test_rate_limit_bloquea_tras_varios_intentos_fallidos():
    email = f"ratelimit-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    codes = []
    for _ in range(6):
        resp = client.post("/api/auth/login", json={"email": email, "password": "incorrecta"})
        codes.append(resp.status_code)
    assert codes[:5] == [401] * 5
    assert codes[5] == 429


def test_rate_limit_es_por_email_no_global():
    """Agotar el límite para un email no debe afectar el login de otro usuario."""
    email = f"ratelimit-aislado-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    for _ in range(6):
        client.post("/api/auth/login", json={"email": email, "password": "incorrecta"})

    resp = client.post(
        "/api/auth/login", json={"email": "admin@dispatchplatform.cl", "password": PASSWORD}
    )
    assert resp.status_code == 200


def test_logins_exitosos_repetidos_nunca_se_bloquean():
    """Solo los intentos FALLIDOS cuentan para el límite — un usuario legítimo
    logueándose varias veces seguidas (o una suite de tests) no debe
    autobloquearse jamás."""
    for _ in range(10):
        resp = client.post(
            "/api/auth/login", json={"email": "despachador@dispatchplatform.cl", "password": PASSWORD}
        )
        assert resp.status_code == 200


def test_crear_chofer_genera_registro_de_auditoria(admin_token):
    email = f"chofer-audit-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    resp = client.post(
        "/api/drivers",
        headers=auth_headers(admin_token),
        json={
            "email": email, "full_name": "Chofer Audit Test", "password": PASSWORD,
            "license_number": f"LIC-{uuid.uuid4().hex[:6]}",
        },
    )
    driver_id = resp.json()["id"]

    logs = client.get("/api/audit-logs?modulo=drivers&limit=50", headers=auth_headers(admin_token)).json()
    assert any(log["registro_id"] == driver_id and log["accion"] == "CREATE" for log in logs)


def test_transicion_de_estado_genera_registro_de_auditoria(admin_token, despachador_token):
    vendedor_token = login("vendedor@dispatchplatform.cl")
    customer = client.post(
        "/api/customers", headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Cliente Audit {uuid.uuid4().hex[:6]}",
            "address": {"nombre": "P", "calle": "C", "comuna": "X", "ciudad": "X", "region": "X", "latitud": -33.5, "longitud": -70.6, "es_principal": True},
        },
    ).json()
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    shipment = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer["id"], "address_id": customer["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-15",
        },
    ).json()

    client.post(
        f"/api/shipments/{shipment['id']}/status",
        headers=auth_headers(despachador_token), json={"nuevo_estado": "PREPARANDO"},
    )

    logs = client.get("/api/audit-logs?modulo=shipments&limit=50", headers=auth_headers(admin_token)).json()
    assert any(
        log["registro_id"] == shipment["id"] and log["valor_nuevo"]["estado"] == "PREPARANDO"
        for log in logs
    )


def test_despachador_no_puede_ver_audit_logs(despachador_token):
    resp = client.get("/api/audit-logs", headers=auth_headers(despachador_token))
    assert resp.status_code == 403


def test_chofer_no_puede_ver_audit_logs():
    chofer_token = login("chofer1@dispatchplatform.cl")
    resp = client.get("/api/audit-logs", headers=auth_headers(chofer_token))
    assert resp.status_code == 403


def test_gps_rate_limit_no_bloquea_uso_normal(admin_token):
    """El límite de GPS (60/min) no debe interferir con un envío normal."""
    email = f"chofer-ratelimit-gps-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    client.post(
        "/api/drivers", headers=auth_headers(admin_token),
        json={"email": email, "full_name": "X", "password": PASSWORD, "license_number": f"L-{uuid.uuid4().hex[:6]}"},
    )
    vehicle = client.post(
        "/api/vehicles", headers=auth_headers(admin_token), json={"plate": f"A{uuid.uuid4().hex[:5].upper()}"}
    ).json()
    driver_token = login(email)
    client.post("/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]})

    resp = client.post(
        "/api/tracking/location", headers=auth_headers(driver_token),
        json={"positions": [{
            "client_uuid": str(uuid.uuid4()), "latitude": -33.5, "longitude": -70.6,
            "recorded_at": "2026-08-12T10:00:00Z",
        }]},
    )
    assert resp.status_code == 200
