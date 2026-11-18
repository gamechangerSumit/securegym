import logging
from dataclasses import dataclass

from app.models.incident import Incident

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    title: str
    message: str
    incident_id: int


class NotificationService:
    """Console fallback. External providers are added behind this interface."""

    def send_incident(self, incident: Incident) -> None:
        alert = Alert(
            title=f"Equipment left unattended: {incident.equipment_class}",
            message=(
                f"Camera {incident.camera_id}; incident #{incident.id}; "
                f"status={incident.status}; attribution={incident.attribution_status}; "
                f"evidence={incident.evidence_path or 'not captured'}"
            ),
            incident_id=incident.id,
        )
        logger.warning("SECUREGYM ALERT | %s | %s", alert.title, alert.message)
