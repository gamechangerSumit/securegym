from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemberSession(Base):
    __tablename__ = "member_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[str] = mapped_column(String(120), index=True)
    member_display_name: Mapped[str] = mapped_column(String(160))
    camera_id: Mapped[int] = mapped_column(index=True)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_recorded: Mapped[bool] = mapped_column(default=False)
