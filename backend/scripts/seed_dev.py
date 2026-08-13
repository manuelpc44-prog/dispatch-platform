"""Seed de datos de desarrollo. NO USAR EN PRODUCCION (ver sección 43 del prompt).

Uso:
    PYTHONPATH=. python3 scripts/seed_dev.py
"""

import datetime
import uuid

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.customer import Customer, CustomerAddress
from app.models.enums import RoleName
from app.models.fleet import Driver, Vehicle, Warehouse
from app.models.shipment import Shipment
from app.models.user import Role, User

ROLE_DESCRIPTIONS = {
    RoleName.ADMINISTRADOR: "Administra usuarios, catálogos y configuración global",
    RoleName.DESPACHADOR: "Asigna despachos a choferes y supervisa el mapa en vivo",
    RoleName.VENDEDOR: "Crea clientes, direcciones y despachos",
    RoleName.CHOFER: "Ejecuta rutas desde la app Android",
    RoleName.CLIENTE: "Consulta sus propios despachos y seguimiento",
}


def get_or_create_role(db, name: RoleName) -> Role:
    role = db.query(Role).filter_by(name=name.value).first()
    if role:
        return role
    role = Role(name=name.value, description=ROLE_DESCRIPTIONS[name])
    db.add(role)
    db.flush()
    return role


def get_or_create_user(db, email: str, full_name: str, role: Role, password: str = "Password123!") -> User:
    user = db.query(User).filter_by(email=email).first()
    if user:
        return user
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
    )
    user.roles.append(role)
    db.add(user)
    db.flush()
    return user


def run() -> None:
    db = SessionLocal()
    try:
        roles = {name: get_or_create_role(db, name) for name in RoleName}
        db.flush()

        admin = get_or_create_user(db, "admin@dispatchplatform.cl", "Admin General", roles[RoleName.ADMINISTRADOR])
        dispatcher = get_or_create_user(
            db, "despachador@dispatchplatform.cl", "Dana Despachadora", roles[RoleName.DESPACHADOR]
        )
        seller = get_or_create_user(db, "vendedor@dispatchplatform.cl", "Vicente Vendedor", roles[RoleName.VENDEDOR])
        driver_user_1 = get_or_create_user(db, "chofer1@dispatchplatform.cl", "Carlos Chofer", roles[RoleName.CHOFER])
        driver_user_2 = get_or_create_user(db, "chofer2@dispatchplatform.cl", "Carla Chofer", roles[RoleName.CHOFER])
        client_user = get_or_create_user(db, "cliente@dispatchplatform.cl", "Camila Cliente", roles[RoleName.CLIENTE])
        db.flush()

        warehouse = db.query(Warehouse).filter_by(name="Bodega Central Melipilla").first()
        if not warehouse:
            warehouse = Warehouse(
                name="Bodega Central Melipilla",
                address="Camino a Melipilla 1234",
                latitud=-33.6890,
                longitud=-71.2150,
            )
            db.add(warehouse)
            db.flush()

        vehicles = []
        for plate, brand, model in [("ABCD12", "Hyundai", "H100"), ("EFGH34", "Chevrolet", "NHR")]:
            v = db.query(Vehicle).filter_by(plate=plate).first()
            if not v:
                v = Vehicle(plate=plate, brand=brand, model=model, capacity_kg=1500)
                db.add(v)
                db.flush()
            vehicles.append(v)

        drivers = []
        for user, license_number in [(driver_user_1, "LIC-0001"), (driver_user_2, "LIC-0002")]:
            d = db.query(Driver).filter_by(user_id=user.id).first()
            if not d:
                d = Driver(
                    user_id=user.id,
                    license_number=license_number,
                    license_expiry=datetime.date(2028, 1, 1),
                )
                db.add(d)
                db.flush()
            drivers.append(d)

        customers_data = [
            ("Ferretería El Tornillo", "Melipilla", -33.6890, -71.2150),
            ("Panadería San Ramón", "Talagante", -33.6630, -70.9280),
            ("Bodega Los Aromos", "Peñaflor", -33.6110, -70.9250),
        ]
        customers = []
        for business_name, comuna, lat, lng in customers_data:
            c = db.query(Customer).filter_by(business_name=business_name).first()
            if not c:
                c = Customer(business_name=business_name, seller_id=seller.id, email=f"{business_name.lower().replace(' ', '.')}@example.cl")
                db.add(c)
                db.flush()
                addr = CustomerAddress(
                    customer_id=c.id,
                    nombre="Casa matriz",
                    calle="Av. Principal 100",
                    comuna=comuna,
                    ciudad=comuna,
                    region="Metropolitana",
                    latitud=lat,
                    longitud=lng,
                    es_principal=True,
                    activa=True,
                )
                db.add(addr)
                db.flush()
                c._seed_address_id = addr.id
            else:
                addr = db.query(CustomerAddress).filter_by(customer_id=c.id, es_principal=True).first()
                c._seed_address_id = addr.id
            customers.append(c)

        existing_shipments = db.query(Shipment).count()
        if existing_shipments == 0:
            today = datetime.date.today()
            for i, customer in enumerate(customers, start=1):
                numero = f"DES-{today.year}-{i:06d}"
                shipment = Shipment(
                    numero=numero,
                    tracking_code=uuid.uuid4(),
                    customer_id=customer.id,
                    address_id=customer._seed_address_id,
                    seller_id=seller.id,
                    warehouse_id=warehouse.id,
                    fecha_programada=today,
                )
                db.add(shipment)

        db.commit()
        print("Seed completado:")
        print(f"  Usuarios: admin={admin.email}, despachador={dispatcher.email}, "
              f"vendedor={seller.email}, choferes=[{driver_user_1.email}, {driver_user_2.email}], "
              f"cliente={client_user.email}")
        print(f"  Bodega: {warehouse.name}")
        print(f"  Vehículos: {[v.plate for v in vehicles]}")
        print(f"  Choferes: {len(drivers)}")
        print(f"  Clientes: {len(customers)}")
        print(f"  Despachos creados en esta corrida: {3 if existing_shipments == 0 else 0} (ya existían: {existing_shipments})")
        print("  Password para todos los usuarios de prueba: Password123!")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
