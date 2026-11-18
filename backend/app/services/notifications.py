import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import get_settings
from app.models.incident import Incident
from app.services.realtime import publish_event

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    title: str
    message: str
    incident_id: int


class NotificationService:
    """Dashboard WebSocket buzzer + optional SMTP email; logs remain the fallback."""

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
        publish_event({
            "type": "equipment_incident",
            "severity": "warning",
            "incident_id": incident.id,
            "title": alert.title,
            "message": alert.message,
            "camera_id": incident.camera_id,
            "equipment_class": incident.equipment_class,
            "evidence_path": incident.evidence_path,
            "buzzer": True,
        })
        self._send_email(alert)

    def _send_email(self, alert: Alert) -> None:
        settings = get_settings()
        if not (settings.smtp_host and settings.alert_email_to):
            return
        message = EmailMessage()
        message["Subject"] = f"[SecureGym] {alert.title}"
        message["From"] = settings.smtp_username or "securegym@localhost"
        message["To"] = settings.alert_email_to
        message.set_content(
            f"{alert.message}\n\nOpen SecureGym dashboard to review the evidence and resolve the incident."
        )
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                smtp.starttls()
                if settings.smtp_username and settings.smtp_password:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            logger.exception("SecureGym email delivery failed for incident %s", alert.incident_id)
