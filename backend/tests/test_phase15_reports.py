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


def _shift_with_positions(admin_token):
    email = f"chofer-report-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    driver = client.post(
        "/api/drivers", headers=auth_headers(admin_token),
        json={"email": email, "full_name": "Chofer Report Test", "password": PASSWORD, "license_number": f"L-{uuid.uuid4().hex[:6]}"},
    ).json()
    vehicle = client.post(
        "/api/vehicles", headers=auth_headers(admin_token), json={"plate": f"R{uuid.uuid4().hex[:5].upper()}"}
    ).json()
    driver_token = login(email)

    shift = client.post(
        "/api/shifts/start", headers=auth_headers(driver_token), json={"vehicle_id": vehicle["id"]}
    ).json()

    client.post(
        "/api/tracking/location", headers=auth_headers(driver_token),
        json={"positions": [
            {"client_uuid": str(uuid.uuid4()), "latitude": -33.689, "longitude": -71.215, "recorded_at": "2026-08-12T09:00:00Z"},
            {"client_uuid": str(uuid.uuid4()), "latitude": -33.663, "longitude": -70.928, "recorded_at": "2026-08-12T09:30:00Z"},
        ]},
    )
    client.post(f"/api/shifts/{shift['id']}/end", headers=auth_headers(driver_token), json={})
    return driver["id"], shift["id"], driver_token


def test_listar_jornadas_calcula_distancia(admin_token, despachador_token):
    driver_id, shift_id, _ = _shift_with_positions(admin_token)
    resp = client.get(f"/api/reports/shifts?driver_id={driver_id}", headers=auth_headers(despachador_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["distancia_km"] > 0
    assert data[0]["estado"] == "FINALIZADA"


def test_replay_de_ruta_devuelve_puntos_en_orden(admin_token, despachador_token):
    _, shift_id, _ = _shift_with_positions(admin_token)
    resp = client.get(f"/api/reports/shifts/{shift_id}/replay", headers=auth_headers(despachador_token))
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) == 2
    assert points[0]["recorded_at"] < points[1]["recorded_at"]


def test_dashboard_devuelve_estadisticas(despachador_token):
    resp = client.get("/api/reports/dashboard", headers=auth_headers(despachador_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "despachos_hoy" in data
    assert "choferes_activos" in data
    assert "distancia_recorrida_km_hoy" in data


def test_chofer_no_puede_ver_reportes(admin_token):
    _, _, driver_token = _shift_with_positions(admin_token)
    resp = client.get("/api/reports/dashboard", headers=auth_headers(driver_token))
    assert resp.status_code == 403


def test_vendedor_no_puede_ver_reportes():
    vendedor_token = login("vendedor@dispatchplatform.cl")
    resp = client.get("/api/reports/dashboard", headers=auth_headers(vendedor_token))
    assert resp.status_code == 403
