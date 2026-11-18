from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CameraCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    stream_url: str = Field(min_length=8, max_length=1000)
    location: str = Field(default="Unspecified", max_length=160)
    enabled: bool = False

    @field_validator("stream_url")
    @classmethod
    def validate_stream_url(cls, value: str) -> str:
        if not value.startswith(("rtsp://", "rtsps://", "http://", "https://")):
            raise ValueError("Stream URL must use RTSP, RTSPS, HTTP or HTTPS")
        return value


class CameraRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    enabled: bool
    status: str
    last_seen_at: datetime | None
    created_at: datetime


class ZoneCreate(BaseModel):
    camera_id: int
    name: str = Field(min_length=2, max_length=120)
    zone_type: str = Field(pattern="^(storage|monitored)$")
    polygon: list[tuple[float, float]] = Field(min_length=3)
    equipment_classes: list[str] = Field(default_factory=list)
    dwell_seconds: int = Field(default=120, ge=5, le=86400)
    confidence_threshold: float = Field(default=0.45, ge=0.05, le=0.99)

    @field_validator("polygon")
    @classmethod
    def validate_normalised_polygon(cls, points):
        if any(not (0 <= x <= 1 and 0 <= y <= 1) for x, y in points):
            raise ValueError("Polygon coordinates must be normalised between 0 and 1")
        return points


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camera_id: int
    name: str
    zone_type: str
    polygon: list
    equipment_classes: list
    dwell_seconds: int
    confidence_threshold: float
    enabled: bool
