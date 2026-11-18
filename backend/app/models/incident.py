from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"), nullable=True)
    equipment_class: Mapped[str] = mapped_column(String(80), index=True)
    track_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(24), default="open", index=True)
    attribution_status: Mapped[str] = mapped_column(String(24), default="unknown")
    attributed_member_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    attribution_note: Mapped[str] = mapped_column(Text, default="No verified member-session match")
    evidence_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    notification_count: Mapped[int] = mapped_column(Integer, default=0)
