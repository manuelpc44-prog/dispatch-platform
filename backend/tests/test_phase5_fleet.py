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


def test_admin_crea_vehiculo(admin_token):
    plate = f"T{uuid.uuid4().hex[:5].upper()}"
    resp = client.post(
        "/api/vehicles", headers=auth_headers(admin_token), json={"plate": plate, "brand": "Test"}
    )
    assert resp.status_code == 201
    assert resp.json()["plate"] == plate


def test_despachador_no_puede_crear_vehiculo(despachador_token):
    resp = client.post(
        "/api/vehicles",
        headers=auth_headers(despachador_token),
        json={"plate": f"T{uuid.uuid4().hex[:5].upper()}"},
    )
    assert resp.status_code == 403


def test_despachador_puede_listar_vehiculos(despachador_token):
    resp = client.get("/api/vehicles", headers=auth_headers(despachador_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_no_se_permite_patente_duplicada(admin_token):
    plate = f"D{uuid.uuid4().hex[:5].upper()}"
    r1 = client.post("/api/vehicles", headers=auth_headers(admin_token), json={"plate": plate})
    assert r1.status_code == 201
    r2 = client.post("/api/vehicles", headers=auth_headers(admin_token), json={"plate": plate})
    assert r2.status_code == 409
    assert r2.json()["detail"]["error"]["code"] == "DUPLICATE_PLATE"


def test_admin_crea_chofer_con_usuario_y_rol(admin_token):
    email = f"chofer-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    resp = client.post(
        "/api/drivers",
        headers=auth_headers(admin_token),
        json={
            "email": email,
            "full_name": "Chofer De Prueba",
            "password": "Password123!",
            "license_number": f"LIC-{uuid.uuid4().hex[:6]}",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == email
    assert data["full_name"] == "Chofer De Prueba"

    # El nuevo chofer debe poder loguearse y tener el rol CHOFER
    token = login(email)
    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert "CHOFER" in me.json()["roles"]


def test_no_se_permite_email_duplicado_al_crear_chofer(admin_token):
    resp = client.post(
        "/api/drivers",
        headers=auth_headers(admin_token),
        json={
            "email": "admin@dispatchplatform.cl",  # ya existe
            "full_name": "Duplicado",
            "password": "Password123!",
            "license_number": "LIC-DUP",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "DUPLICATE_EMAIL"


def test_vendedor_no_puede_crear_chofer():
    vendedor_token = login("vendedor@dispatchplatform.cl")
    resp = client.post(
        "/api/drivers",
        headers=auth_headers(vendedor_token),
        json={
            "email": f"x-{uuid.uuid4().hex[:6]}@dispatchplatform.cl",
            "full_name": "X",
            "password": "Password123!",
            "license_number": "LIC-X",
        },
    )
    assert resp.status_code == 403


def test_admin_crea_bodega(admin_token):
    resp = client.post(
        "/api/warehouses",
        headers=auth_headers(admin_token),
        json={"name": f"Bodega Test {uuid.uuid4().hex[:6]}", "latitud": -33.5, "longitud": -70.6},
    )
    assert resp.status_code == 201
