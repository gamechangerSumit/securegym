import base64
import binascii
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings


def save_jpeg_evidence(*, camera_id: int, incident_id: int, image_base64: str | None) -> str | None:
    """Persist a JPEG frame supplied by an authorised camera worker.

    Returns a relative path; never accepts a caller-supplied filesystem path.
    """
    if not image_base64:
        return None
    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Evidence must be valid base64 JPEG data") from exc
    if not image_bytes.startswith(b"\xff\xd8\xff"):
        raise ValueError("Evidence payload is not a JPEG image")
    if len(image_bytes) > 8 * 1024 * 1024:
        raise ValueError("Evidence image exceeds 8 MB limit")

    now = datetime.now(timezone.utc)
    directory = get_settings().evidence_dir / now.strftime("%Y/%m/%d")
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"cam-{camera_id}-incident-{incident_id}-{uuid4().hex[:8]}.jpg"
    destination = directory / filename
    destination.write_bytes(image_bytes)
    return str(destination)
