from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident import Incident


def upsert_equipment_incident(
    db: Session,
    *,
    camera_id: int,
    zone_id: int,
    equipment_class: str,
    track_id: str | None,
    confidence: float,
    evidence_path: str | None = None,
) -> tuple[Incident, bool]:
    """Deduplicate an open incident for the same camera, zone and current track."""
    query = select(Incident).where(
        Incident.camera_id == camera_id,
        Incident.zone_id == zone_id,
        Incident.equipment_class == equipment_class,
        Incident.status.in_(["open", "acknowledged"]),
    )
    if track_id is None:
        query = query.where(Incident.track_id.is_(None))
    else:
        query = query.where(Incident.track_id == track_id)

    incident = db.scalar(query.order_by(Incident.id.desc()).limit(1))
    now = datetime.now(timezone.utc)
    if incident:
        incident.last_detected_at = now
        incident.confidence = max(incident.confidence, confidence)
        if evidence_path and not incident.evidence_path:
            incident.evidence_path = evidence_path
        db.commit()
        db.refresh(incident)
        return incident, False

    incident = Incident(
        camera_id=camera_id,
        zone_id=zone_id,
        equipment_class=equipment_class,
        track_id=track_id,
        confidence=confidence,
        evidence_path=evidence_path,
        first_detected_at=now,
        last_detected_at=now,
        attribution_status="unknown",
        attribution_note="No verified member-session match; camera track is not a member identity",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident, True
