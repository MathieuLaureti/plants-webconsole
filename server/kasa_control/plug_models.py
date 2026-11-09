import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _validate_hhmm(value: str) -> str:
    if not TIME_RE.match(value):
        raise ValueError("expected HH:MM (24h)")
    return value


class SimpleSchedule(BaseModel):
    morning_time: str
    night_time: str
    day_pulse_count: int = Field(ge=1, le=500)
    night_pulse_count: int = Field(ge=1, le=500)
    pulse_seconds: int = Field(ge=1, le=3600)

    @field_validator("morning_time", "night_time")
    @classmethod
    def check_time(cls, value: str) -> str:
        return _validate_hhmm(value)


class AdvancedSchedule(BaseModel):
    pulse_seconds: int = Field(ge=1, le=3600)
    times: list[str] = Field(min_length=1, max_length=200)

    @field_validator("times")
    @classmethod
    def check_times(cls, values: list[str]) -> list[str]:
        return [_validate_hhmm(v) for v in values]


class StaticSchedule(BaseModel):
    activate_time: str
    deactivate_time: str

    @field_validator("activate_time", "deactivate_time")
    @classmethod
    def check_time(cls, value: str) -> str:
        return _validate_hhmm(value)


class PlugCreate(BaseModel):
    host: str = Field(min_length=1, max_length=253)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    schedule_type: Literal["simple", "advanced", "static"]
    schedule: dict[str, Any]

    @field_validator("host")
    @classmethod
    def strip_host(cls, value: str) -> str:
        return value.strip()


class PlugUpdate(BaseModel):
    host: str | None = Field(default=None, min_length=1, max_length=253)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    schedule_type: Literal["simple", "advanced", "static"] | None = None
    schedule: dict[str, Any] | None = None


class ScheduleEnabledUpdate(BaseModel):
    enabled: bool


class PlugPing(BaseModel):
    host: str = Field(min_length=1, max_length=253)

    @field_validator("host")
    @classmethod
    def strip_host(cls, value: str) -> str:
        return value.strip()


def validate_schedule_for_type(
    schedule_type: str, schedule: dict
) -> SimpleSchedule | AdvancedSchedule | StaticSchedule:
    if schedule_type == "simple":
        return SimpleSchedule.model_validate(schedule)
    if schedule_type == "advanced":
        return AdvancedSchedule.model_validate(schedule)
    return StaticSchedule.model_validate(schedule)
