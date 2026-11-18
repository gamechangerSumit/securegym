from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Camera, EquipmentPresence, Zone
from app.models.incident import Incident
from app.schemas.incident_observation import EquipmentObservation
from app.services.evidence import save_jpeg_evidence
from app.services.incident_engine import upsert_equipment_incident
from app.services.notifications import NotificationService

notifications = NotificationService()


def process_observation(db: Session, observation: EquipmentObservation) -> tuple[Incident | None, bool]:
    """Require continuous sightings for the configured dwell period before alerting."""
    camera = db.get(Camera, observation.camera_id)
    zone = db.get(Zone, observation.zone_id)
    if camera is None or zone is None or zone.camera_id != observation.camera_id:
        raise ValueError("Observation references an unknown camera/zone pair")
    if not camera.enabled or not zone.enabled:
        return None, False
    if zone.zone_type != "storage":
        raise ValueError("Observation zone must be a storage zone")

    track_key = observation.track_id or "untracked"
    query = select(EquipmentPresence).where(
        EquipmentPresence.camera_id == camera.id,
        EquipmentPresence.zone_id == zone.id,
        EquipmentPresence.equipment_class == observation.equipment_class,
        EquipmentPresence.track_id == track_key,
    )
    presence = db.scalar(query)
    observed_at = datetime.fromtimestamp(observation.observed_at_epoch, tz=timezone.utc)

    if not observation.outside_storage:
        active_query = select(Incident).where(
            Incident.camera_id == camera.id,
            Incident.zone_id == zone.id,
            Incident.equipment_class == observation.equipment_class,
            Incident.status.in_(["open", "acknowledged"]),
        )
        if observation.track_id is None:
            active_query = active_query.where(Incident.track_id.is_(None))
        else:
            active_query = active_query.where(Incident.track_id == observation.track_id)
        active_incident = db.scalar(active_query.order_by(Incident.id.desc()).limit(1))
        if active_incident:
            active_incident.status = "resolved"
            active_incident.resolved_at = observed_at
            active_incident.resolution_note = "Vision system observed equipment returned to storage zone"
        if presence:
            db.delete(presence)
        db.commit()
        return active_incident, False

    if observation.confidence < zone.confidence_threshold:
        return None, False
    if zone.equipment_classes and observation.equipment_class not in zone.equipment_classes:
        return None, False

    if presence is None:
        presence = EquipmentPresence(
            camera_id=camera.id,
            zone_id=zone.id,
            equipment_class=observation.equipment_class,
            track_id=track_key,
            first_outside_at=observed_at,
            last_seen_at=observed_at,
        )
        db.add(presence)
        db.commit()
        db.refresh(presence)
        return None, False

    gap_seconds = (observed_at - presence.last_seen_at).total_seconds()
    if gap_seconds > max(15, zone.dwell_seconds / 2):
        presence.first_outside_at = observed_at
        presence.incident_created = False
    presence.last_seen_at = observed_at
    elapsed = (observed_at - presence.first_outside_at).total_seconds()

    if elapsed < zone.dwell_seconds or presence.incident_created:
        db.commit()
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
            incident.evidence_path = None

    presence.incident_created = True
    db.commit()
    db.refresh(incident)
    if created:
        notifications.send_incident(incident)
        incident.notification_count += 1
        db.commit()
        db.refresh(incident)
    return incident, created
