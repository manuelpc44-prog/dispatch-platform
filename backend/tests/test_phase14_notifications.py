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


@pytest.fixture
def cliente_con_login(vendedor_token):
    """Crea un Customer con user_id vinculado a un usuario CLIENTE recién creado,
    para poder verificar que las notificaciones le llegan."""
    from app.db.session import SessionLocal
    from app.models.customer import Customer
    from app.models.enums import RoleName
    from app.models.user import Role, User
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        email = f"cliente-notif-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
        role = db.query(Role).filter(Role.name == RoleName.CLIENTE.value).first()
        user = User(email=email, password_hash=hash_password(PASSWORD), full_name="Cliente Notif Test", is_active=True)
        user.roles.append(role)
        db.add(user)
        db.flush()

        customer_resp = client.post(
            "/api/customers",
            headers=auth_headers(vendedor_token),
            json={
                "business_name": f"Cliente Notif {uuid.uuid4().hex[:6]}",
                "address": {
                    "nombre": "P", "calle": "C", "comuna": "X", "ciudad": "X", "region": "X",
                    "latitud": -33.5, "longitud": -70.6, "es_principal": True,
                },
            },
        ).json()
        customer = db.query(Customer).filter(Customer.id == customer_resp["id"]).first()
        customer.user_id = user.id
        db.commit()

        token = login(email)
        return {"token": token, "customer": customer_resp}
    finally:
        db.close()


def test_registrar_device_token(despachador_token):
    resp = client.post(
        "/api/notifications/register-device",
        headers=auth_headers(despachador_token),
        json={"token": f"tok-{uuid.uuid4().hex}", "platform": "android"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "registered"


def test_registrar_mismo_token_dos_veces_no_falla(despachador_token):
    token_value = f"tok-{uuid.uuid4().hex}"
    r1 = client.post(
        "/api/notifications/register-device", headers=auth_headers(despachador_token),
        json={"token": token_value, "platform": "android"},
    )
    r2 = client.post(
        "/api/notifications/register-device", headers=auth_headers(despachador_token),
        json={"token": token_value, "platform": "android"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201


def test_crear_despacho_notifica_al_cliente(vendedor_token, despachador_token, cliente_con_login):
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    customer = cliente_con_login["customer"]

    resp = client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer["id"], "address_id": customer["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-15",
        },
    )
    assert resp.status_code == 201

    notifications = client.get(
        "/api/notifications", headers=auth_headers(cliente_con_login["token"])
    ).json()
    assert any(n["tipo"] == "SHIPMENT_CREADO" for n in notifications)


def test_transicion_a_asignado_notifica_al_cliente(vendedor_token, despachador_token, cliente_con_login):
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    customer = cliente_con_login["customer"]
    shipment = client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer["id"], "address_id": customer["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-15",
        },
    ).json()

    for estado in ["PREPARANDO", "LISTO", "ASIGNADO"]:
        client.post(
            f"/api/shipments/{shipment['id']}/status",
            headers=auth_headers(despachador_token),
            json={"nuevo_estado": estado},
        )

    notifications = client.get(
        "/api/notifications", headers=auth_headers(cliente_con_login["token"])
    ).json()
    tipos = {n["tipo"] for n in notifications}
    assert "SHIPMENT_CREADO" in tipos
    assert "SHIPMENT_ASIGNADO" in tipos


def test_marcar_notificacion_como_leida(vendedor_token, despachador_token, cliente_con_login):
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    customer = cliente_con_login["customer"]
    client.post(
        "/api/shipments",
        headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer["id"], "address_id": customer["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-15",
        },
    )
    token = cliente_con_login["token"]
    notification_id = client.get("/api/notifications", headers=auth_headers(token)).json()[0]["id"]

    resp = client.patch(f"/api/notifications/{notification_id}/read", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["leido"] is True

    unread = client.get("/api/notifications?unread_only=true", headers=auth_headers(token)).json()
    assert notification_id not in [n["id"] for n in unread]


def test_push_provider_sin_credenciales_no_rompe_el_flujo():
    """Verifica que, sin FCM_CREDENTIALS configurado, el NullPushProvider
    responde sin lanzar excepciones (comportamiento de fallback de Fase 14)."""
    from app.services.push_service import NullPushProvider

    provider = NullPushProvider()
    result = provider.send("cualquier-token", "Título", "Cuerpo")
    assert result.sent is False
    assert result.detail == "FCM_NOT_CONFIGURED"


def test_get_push_provider_usa_null_provider_por_defecto():
    from app.core.config import settings
    from app.services.push_service import NullPushProvider, get_push_provider

    assert settings.fcm_credentials is None
    provider = get_push_provider()
    assert isinstance(provider, NullPushProvider)
