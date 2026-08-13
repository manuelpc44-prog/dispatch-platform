import io
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


@pytest.fixture
def vendedor_token():
    return login("vendedor@dispatchplatform.cl")


def _shipment_in_entrega_en_proceso(admin_token, despachador_token, vendedor_token):
    """Crea chofer+vehículo+despacho y lo lleva hasta ENTREGA_EN_PROCESO."""
    email = f"chofer-delivery-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    driver = client.post(
        "/api/drivers",
        headers=auth_headers(admin_token),
        json={
            "email": email, "full_name": "Chofer Test", "password": PASSWORD,
            "license_number": f"LIC-{uuid.uuid4().hex[:6]}",
        },
    ).json()
    vehicle = client.post(
        "/api/vehicles", headers=auth_headers(admin_token),
        json={"plate": f"D{uuid.uuid4().hex[:5].upper()}"},
    ).json()
    driver_token = login(email)

    customer = client.post(
        "/api/customers",
        headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Cliente Delivery {uuid.uuid4().hex[:6]}",
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
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-10",
        },
    ).json()
    shipment_id = shipment["id"]

    for estado in ["PREPARANDO", "LISTO"]:
        client.post(f"/api/shipments/{shipment_id}/status", headers=auth_headers(despachador_token), json={"nuevo_estado": estado})

    client.post(
        "/api/routes",
        headers=auth_headers(despachador_token),
        json={
            "driver_id": driver["id"], "vehicle_id": vehicle["id"], "warehouse_id": warehouse_id,
            "fecha": "2026-08-10", "shipment_ids": [shipment_id],
        },
    )
    for estado in ["SALIDA_BODEGA", "EN_RUTA", "LLEGADA_CLIENTE", "ENTREGA_EN_PROCESO"]:
        client.post(f"/api/shipments/{shipment_id}/status", headers=auth_headers(despachador_token), json={"nuevo_estado": estado})

    return shipment_id, driver_token


def test_chofer_ve_su_despacho_asignado(admin_token, despachador_token, vendedor_token):
    shipment_id, driver_token = _shipment_in_entrega_en_proceso(admin_token, despachador_token, vendedor_token)
    resp = client.get(f"/api/shipments/{shipment_id}", headers=auth_headers(driver_token))
    assert resp.status_code == 200
    assert resp.json()["estado"] == "ENTREGA_EN_PROCESO"


def test_subir_evidencia_y_registrar_entrega_exitosa(admin_token, despachador_token, vendedor_token):
    shipment_id, driver_token = _shipment_in_entrega_en_proceso(admin_token, despachador_token, vendedor_token)

    upload = client.post(
        "/api/deliveries/evidence",
        headers=auth_headers(driver_token),
        files={"file": ("foto.jpg", io.BytesIO(b"contenido-de-prueba"), "image/jpeg")},
    )
    assert upload.status_code == 201
    evidence_url = upload.json()["url"]

    delivery = client.post(
        "/api/deliveries",
        headers=auth_headers(driver_token),
        json={
            "shipment_id": shipment_id, "resultado": "ENTREGADO", "receptor_nombre": "Juan Pérez",
            "evidence": [{"tipo": "FOTO", "url": evidence_url}],
        },
    )
    assert delivery.status_code == 201, delivery.text
    assert delivery.json()["evidence"][0]["url"] == evidence_url

    shipment = client.get(f"/api/shipments/{shipment_id}", headers=auth_headers(driver_token)).json()
    assert shipment["estado"] == "ENTREGADO"

    media_resp = client.get(evidence_url)
    assert media_resp.status_code == 200


def test_no_se_permite_extension_no_permitida(admin_token, despachador_token, vendedor_token):
    _, driver_token = _shipment_in_entrega_en_proceso(admin_token, despachador_token, vendedor_token)
    resp = client.post(
        "/api/deliveries/evidence",
        headers=auth_headers(driver_token),
        files={"file": ("archivo.exe", io.BytesIO(b"malicioso"), "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "INVALID_UPLOAD"


def test_registrar_entrega_no_exitosa_con_motivo(admin_token, despachador_token, vendedor_token):
    shipment_id, driver_token = _shipment_in_entrega_en_proceso(admin_token, despachador_token, vendedor_token)
    resp = client.post(
        "/api/deliveries",
        headers=auth_headers(driver_token),
        json={"shipment_id": shipment_id, "resultado": "NO_ENTREGADO", "motivo_fallo": "Cliente ausente"},
    )
    assert resp.status_code == 201
    shipment = client.get(f"/api/shipments/{shipment_id}", headers=auth_headers(driver_token)).json()
    assert shipment["estado"] == "NO_ENTREGADO"


def test_no_se_puede_registrar_dos_entregas_para_el_mismo_despacho(admin_token, despachador_token, vendedor_token):
    shipment_id, driver_token = _shipment_in_entrega_en_proceso(admin_token, despachador_token, vendedor_token)
    client.post(
        "/api/deliveries", headers=auth_headers(driver_token),
        json={"shipment_id": shipment_id, "resultado": "ENTREGADO"},
    )
    resp2 = client.post(
        "/api/deliveries", headers=auth_headers(driver_token),
        json={"shipment_id": shipment_id, "resultado": "ENTREGADO"},
    )
    assert resp2.status_code == 409
    assert resp2.json()["detail"]["error"]["code"] == "DELIVERY_ALREADY_EXISTS"


def test_chofer_no_asignado_no_puede_ver_ni_actuar_sobre_despacho_ajeno(despachador_token, vendedor_token, admin_token):
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    customer = client.post(
        "/api/customers", headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Cliente Ajeno {uuid.uuid4().hex[:6]}",
            "address": {"nombre": "P", "calle": "C", "comuna": "X", "ciudad": "X", "region": "X", "latitud": -33.5, "longitud": -70.6, "es_principal": True},
        },
    ).json()
    shipment = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer["id"], "address_id": customer["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-10",
        },
    ).json()
    # No se asigna a ningún chofer (queda en PENDIENTE, driver_id nulo)
    email = f"chofer-ajeno-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    client.post(
        "/api/drivers", headers=auth_headers(admin_token),
        json={"email": email, "full_name": "X", "password": PASSWORD, "license_number": f"L-{uuid.uuid4().hex[:6]}"},
    )
    driver_token = login(email)

    # No puede verlo (RBAC lo oculta por completo — comportamiento correcto, no
    # revela si el despacho existe o si simplemente no le pertenece)
    get_resp = client.get(f"/api/shipments/{shipment['id']}", headers=auth_headers(driver_token))
    assert get_resp.status_code == 404

    delivery_resp = client.post(
        "/api/deliveries", headers=auth_headers(driver_token),
        json={"shipment_id": shipment["id"], "resultado": "ENTREGADO"},
    )
    assert delivery_resp.status_code == 404


def test_chofer_asignado_no_puede_entregar_si_despacho_no_llego_a_entrega_en_proceso(admin_token, despachador_token, vendedor_token):
    email = f"chofer-temprano-{uuid.uuid4().hex[:8]}@dispatchplatform.cl"
    driver = client.post(
        "/api/drivers", headers=auth_headers(admin_token),
        json={"email": email, "full_name": "X", "password": PASSWORD, "license_number": f"L-{uuid.uuid4().hex[:6]}"},
    ).json()
    vehicle = client.post(
        "/api/vehicles", headers=auth_headers(admin_token), json={"plate": f"E{uuid.uuid4().hex[:5].upper()}"}
    ).json()
    driver_token = login(email)

    customer = client.post(
        "/api/customers", headers=auth_headers(vendedor_token),
        json={
            "business_name": f"Cliente Temprano {uuid.uuid4().hex[:6]}",
            "address": {"nombre": "P", "calle": "C", "comuna": "X", "ciudad": "X", "region": "X", "latitud": -33.5, "longitud": -70.6, "es_principal": True},
        },
    ).json()
    warehouse_id = client.get("/api/warehouses", headers=auth_headers(despachador_token)).json()[0]["id"]
    shipment = client.post(
        "/api/shipments", headers=auth_headers(vendedor_token),
        json={
            "customer_id": customer["id"], "address_id": customer["addresses"][0]["id"],
            "warehouse_id": warehouse_id, "fecha_programada": "2026-08-10",
        },
    ).json()
    for estado in ["PREPARANDO", "LISTO"]:
        client.post(f"/api/shipments/{shipment['id']}/status", headers=auth_headers(despachador_token), json={"nuevo_estado": estado})
    client.post(
        "/api/routes", headers=auth_headers(despachador_token),
        json={
            "driver_id": driver["id"], "vehicle_id": vehicle["id"], "warehouse_id": warehouse_id,
            "fecha": "2026-08-10", "shipment_ids": [shipment["id"]],
        },
    )
    # Ahora SÍ está asignado a este chofer, pero el despacho quedó en ASIGNADO,
    # no en ENTREGA_EN_PROCESO
    resp = client.post(
        "/api/deliveries", headers=auth_headers(driver_token),
        json={"shipment_id": shipment["id"], "resultado": "ENTREGADO"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "SHIPMENT_NOT_IN_DELIVERY_STATE"


def test_despachador_no_puede_registrar_entrega(admin_token, despachador_token, vendedor_token):
    shipment_id, _ = _shipment_in_entrega_en_proceso(admin_token, despachador_token, vendedor_token)
    resp = client.post(
        "/api/deliveries", headers=auth_headers(despachador_token),
        json={"shipment_id": shipment_id, "resultado": "ENTREGADO"},
    )
    assert resp.status_code == 403


def test_chofer_reporta_incidencia(admin_token, despachador_token, vendedor_token):
    shipment_id, driver_token = _shipment_in_entrega_en_proceso(admin_token, despachador_token, vendedor_token)
    resp = client.post(
        "/api/incidents", headers=auth_headers(driver_token),
        json={"shipment_id": shipment_id, "tipo": "Problema vehículo", "descripcion": "Pinchazo"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["tipo"] == "Problema vehículo"

    shipment = client.get(f"/api/shipments/{shipment_id}", headers=auth_headers(driver_token)).json()
    assert shipment["estado"] == "INCIDENCIA"

    history = client.get(f"/api/incidents/by-shipment/{shipment_id}", headers=auth_headers(driver_token)).json()
    assert len(history) == 1
