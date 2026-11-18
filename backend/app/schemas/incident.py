from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camera_id: int
    zone_id: int | None
    equipment_class: str
    track_id: str | None
    confidence: float
    status: str
    attribution_status: str
    attributed_member_id: str | None
    attribution_note: str
    evidence_path: str | None
    first_detected_at: datetime
    last_detected_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    resolution_note: str | None
    notification_count: int


class IncidentResolve(BaseModel):
    note: str = "Equipment returned to its designated storage area"


class DashboardSummary(BaseModel):
    cameras_total: int
    cameras_online: int
    open_incidents: int
    acknowledged_incidents: int
    resolved_today: int
