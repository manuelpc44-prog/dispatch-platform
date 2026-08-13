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
def chofer_token():
    return login("chofer1@dispatchplatform.cl")


@pytest.fixture
def admin_token():
    return login("admin@dispatchplatform.cl")


def test_vendedor_puede_crear_cliente_con_direccion_geocodificada(vendedor_token):
    resp = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={
            "business_name": "Cliente Test Fase 4",
            "address": {
                "nombre": "Casa matriz",
                "calle": "Calle Falsa",
                "numero": "123",
                "comuna": "Melipilla",
                "ciudad": "Melipilla",
                "region": "Metropolitana",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert len(data["addresses"]) == 1
    # Geocodificado automáticamente: no debe ser null ni (0,0)
    addr = data["addresses"][0]
    assert addr["latitud"] is not None
    assert addr["longitud"] is not None
    assert float(addr["latitud"]) != 0.0


def test_chofer_no_puede_crear_cliente(chofer_token):
    resp = client.post(
        "/api/customers",
        headers=auth_headers(chofer_token),
        json={"business_name": "No debería crearse"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"


def test_vendedor_solo_ve_sus_propios_clientes(vendedor_token, admin_token):
    # Crear un cliente asignado a este vendedor
    create_resp = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={"business_name": "Cliente Aislamiento Test"},
    )
    assert create_resp.status_code == 201

    listado = client.get("/api/customers", headers=auth_headers(vendedor_token))
    assert listado.status_code == 200
    nombres = [c["business_name"] for c in listado.json()]
    assert "Cliente Aislamiento Test" in nombres

    # El admin también debe poder verlo (ve todos)
    listado_admin = client.get("/api/customers", headers=auth_headers(admin_token))
    nombres_admin = [c["business_name"] for c in listado_admin.json()]
    assert "Cliente Aislamiento Test" in nombres_admin


def test_cliente_no_ve_clientes_de_otros(vendedor_token):
    cliente_token = login("cliente@dispatchplatform.cl")
    resp = client.get("/api/customers", headers=auth_headers(cliente_token))
    assert resp.status_code == 200
    # El usuario CLIENTE del seed no tiene Customer.user_id vinculado -> no ve nada,
    # en particular no ve los clientes creados por el vendedor
    assert resp.json() == []


def test_una_sola_direccion_principal_por_cliente(vendedor_token):
    create_resp = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={"business_name": "Cliente Principal Test"},
    )
    customer_id = create_resp.json()["id"]

    addr1 = client.post(
        f"/api/customers/{customer_id}/addresses",
        headers=auth_headers(vendedor_token),
        json={
            "nombre": "Dirección 1", "calle": "Calle 1", "comuna": "X", "ciudad": "X",
            "region": "X", "latitud": -33.5, "longitud": -70.6, "es_principal": True,
        },
    )
    assert addr1.status_code == 201
    assert addr1.json()["es_principal"] is True

    addr2 = client.post(
        f"/api/customers/{customer_id}/addresses",
        headers=auth_headers(vendedor_token),
        json={
            "nombre": "Dirección 2", "calle": "Calle 2", "comuna": "X", "ciudad": "X",
            "region": "X", "latitud": -33.6, "longitud": -70.7, "es_principal": True,
        },
    )
    assert addr2.status_code == 201
    assert addr2.json()["es_principal"] is True

    listado = client.get(
        f"/api/customers/{customer_id}/addresses", headers=auth_headers(vendedor_token)
    ).json()
    principales = [a for a in listado if a["es_principal"]]
    assert len(principales) == 1
    assert principales[0]["nombre"] == "Dirección 2"


def test_geocodificacion_es_determinística_para_la_misma_direccion():
    from app.services.geocoding import get_geocoding_provider

    provider = get_geocoding_provider()
    r1 = provider.geocode("Av. Siempre Viva", "742", "Springfield", "Springfield", "X")
    r2 = provider.geocode("Av. Siempre Viva", "742", "Springfield", "Springfield", "X")
    assert r1.latitude == r2.latitude
    assert r1.longitude == r2.longitude


def test_no_se_puede_ver_cliente_de_otro_vendedor():
    vendedor1 = login("vendedor@dispatchplatform.cl")
    create_resp = client.post(
        "/api/customers",
        headers=auth_headers(vendedor1),
        json={"business_name": "Cliente Privado Vendedor 1"},
    )
    customer_id = create_resp.json()["id"]

    # Un chofer intentando ver el detalle del cliente por id -> no lo encuentra (403/404 según scope)
    chofer_token = login("chofer1@dispatchplatform.cl")
    resp = client.get(f"/api/customers/{customer_id}", headers=auth_headers(chofer_token))
    assert resp.status_code == 404
