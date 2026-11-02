from pydantic import BaseModel, Field


class PlugScheduleUpdate(BaseModel):
    enabled: bool
    interval_minutes: int = Field(default=5, ge=1, le=24 * 60)
    on_minutes: int = Field(default=1, ge=1, le=24 * 60)
