from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EquipmentPresence(Base):
    __tablename__ = "equipment_presence"
    __table_args__ = (
        UniqueConstraint("camera_id", "zone_id", "equipment_class", "track_id", name="uq_equipment_presence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), index=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id", ondelete="CASCADE"), index=True)
    equipment_class: Mapped[str] = mapped_column(String(80))
    track_id: Mapped[str] = mapped_column(String(80), default="untracked")
    outside_storage: Mapped[bool] = mapped_column(Boolean, default=True)
    first_outside_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    incident_created: Mapped[bool] = mapped_column(Boolean, default=False)
