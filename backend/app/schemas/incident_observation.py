from pydantic import BaseModel, Field


class EquipmentObservation(BaseModel):
    """Internal/event-ingest observation emitted by a camera vision worker."""

    camera_id: int
    zone_id: int
    equipment_class: str = Field(min_length=2, max_length=80)
    track_id: str | None = Field(default=None, max_length=80)
    confidence: float = Field(ge=0.0, le=1.0)
    outside_storage: bool
    observed_at_epoch: float = Field(gt=0)
    evidence_jpeg_base64: str | None = None
