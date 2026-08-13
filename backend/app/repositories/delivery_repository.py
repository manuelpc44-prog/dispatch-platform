import uuid

from sqlalchemy.orm import Session, selectinload

from app.models.delivery import Delivery, DeliveryEvidence
from app.models.misc import Incident


class DeliveryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_shipment(self, shipment_id: uuid.UUID) -> Delivery | None:
        return (
            self.db.query(Delivery)
            .options(selectinload(Delivery.evidence))
            .filter(Delivery.shipment_id == shipment_id)
            .first()
        )

    def create(self, delivery: Delivery) -> Delivery:
        self.db.add(delivery)
        self.db.flush()
        return delivery

    def add_evidence(self, evidence: DeliveryEvidence) -> DeliveryEvidence:
        self.db.add(evidence)
        self.db.flush()
        return evidence


class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, incident: Incident) -> Incident:
        self.db.add(incident)
        self.db.flush()
        return incident

    def list_for_shipment(self, shipment_id: uuid.UUID) -> list[Incident]:
        return (
            self.db.query(Incident)
            .filter(Incident.shipment_id == shipment_id)
            .order_by(Incident.created_at)
            .all()
        )
