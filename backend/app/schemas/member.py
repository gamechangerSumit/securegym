from datetime import datetime

from pydantic import BaseModel, Field


class MemberSessionCreate(BaseModel):
    member_id: str = Field(min_length=1, max_length=120)
    member_display_name: str = Field(min_length=1, max_length=160)
    camera_id: int
    consent_recorded: bool = False


class ManualAttribution(BaseModel):
    member_id: str = Field(min_length=1, max_length=120)
    note: str = Field(min_length=5, max_length=500)


class MemberSessionRead(BaseModel):
    id: int
    member_id: str
    member_display_name: str
    camera_id: int
    checked_in_at: datetime
    checked_out_at: datetime | None
    consent_recorded: bool
