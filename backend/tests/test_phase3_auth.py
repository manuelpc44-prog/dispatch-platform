import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PASSWORD = "Password123!"


@pytest.mark.parametrize(
    "email,expected_role",
    [
        ("admin@dispatchplatform.cl", "ADMINISTRADOR"),
        ("despachador@dispatchplatform.cl", "DESPACHADOR"),
        ("vendedor@dispatchplatform.cl", "VENDEDOR"),
        ("chofer1@dispatchplatform.cl", "CHOFER"),
        ("cliente@dispatchplatform.cl", "CLIENTE"),
    ],
)
def test_login_para_cada_rol_del_seed(email, expected_role):
    resp = client.post("/api/auth/login", json={"email": email, "password": VALID_PASSWORD})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    assert expected_role in me.json()["roles"]


def test_login_con_password_incorrecta_devuelve_401():
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@dispatchplatform.cl", "password": "incorrecta"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_con_email_inexistente_devuelve_401():
    resp = client.post(
        "/api/auth/login",
        json={"email": "no-existe@dispatchplatform.cl", "password": VALID_PASSWORD},
    )
    assert resp.status_code == 401


def test_acceso_sin_token_devuelve_401():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_acceso_con_token_invalido_devuelve_401():
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer token-invalido"})
    assert resp.status_code == 401


def test_endpoint_admin_bloqueado_para_otros_roles():
    login = client.post(
        "/api/auth/login",
        json={"email": "vendedor@dispatchplatform.cl", "password": VALID_PASSWORD},
    )
    token = login.json()["access_token"]
    resp = client.get("/api/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"


def test_endpoint_admin_permitido_para_administrador():
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@dispatchplatform.cl", "password": VALID_PASSWORD},
    )
    token = login.json()["access_token"]
    resp = client.get("/api/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_refresh_token_emite_nuevo_access_token():
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@dispatchplatform.cl", "password": VALID_PASSWORD},
    )
    refresh_token = login.json()["refresh_token"]
    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_access_token_no_sirve_como_refresh_token():
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@dispatchplatform.cl", "password": VALID_PASSWORD},
    )
    access_token = login.json()["access_token"]
    resp = client.post("/api/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
