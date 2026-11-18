import base64
from sqlalchemy.orm import Session

from app.models import Camera, Zone
from app.models.incident import Incident
from app.schemas.incident_observation import EquipmentObservation
from app.services.evidence import save_jpeg_evidence
from app.services.incident_engine import upsert_equipment_incident
from app.services.notifications import NotificationService

notifications = NotificationService()


def process_observation(db: Session, observation: EquipmentObservation) -> tuple[Incident | None, bool]:
    """Apply configured thresholds, record evidence and alert on new misplaced equipment."""
    camera = db.get(Camera, observation.camera_id)
    zone = db.get(Zone, observation.zone_id)
    if camera is None or zone is None or zone.camera_id != observation.camera_id:
        raise ValueError("Observation references an unknown camera/zone pair")
    if not camera.enabled or not zone.enabled:
        return None, False
    if zone.zone_type != "storage":
        raise ValueError("Observation zone must be a storage zone")
    if not observation.outside_storage:
        return None, False
    if observation.confidence < zone.confidence_threshold:
        return None, False
    if zone.equipment_classes and observation.equipment_class not in zone.equipment_classes:
        return None, False

    incident, created = upsert_equipment_incident(
        db,
        camera_id=camera.id,
        zone_id=zone.id,
        equipment_class=observation.equipment_class,
        track_id=observation.track_id,
        confidence=observation.confidence,
    )
    if created and observation.evidence_jpeg_base64:
        try:
            incident.evidence_path = save_jpeg_evidence(
                camera_id=camera.id,
                incident_id=incident.id,
                image_base64=observation.evidence_jpeg_base64,
            )
        except ValueError:
            # Keep the incident even if an invalid evidence frame was supplied.
            incident.evidence_path = None
        db.commit()
        db.refresh(incident)

    if created:
        notifications.send_incident(incident)
        incident.notification_count += 1
        db.commit()
        db.refresh(incident)
    return incident, created
