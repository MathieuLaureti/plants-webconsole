"""Compute pulse windows and runtime countdown from schedule profiles."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from kasa_control.plug_models import AdvancedSchedule, SimpleSchedule


def get_tz() -> ZoneInfo:
    name = os.environ.get("TZ", "America/Toronto")
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("America/Toronto")


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


def _time_to_seconds(value: str) -> int:
    h, m = _parse_hhmm(value)
    return h * 3600 + m * 60


def _window_len_seconds(start_hhmm: str, end_hhmm: str) -> int:
    start = _time_to_seconds(start_hhmm)
    end = _time_to_seconds(end_hhmm)
    if end > start:
        return end - start
    return 24 * 3600 - (start - end)


def validate_schedule_capacity(
    schedule_type: str, schedule: SimpleSchedule | AdvancedSchedule
) -> str | None:
    if schedule_type == "advanced":
        assert isinstance(schedule, AdvancedSchedule)
        return None
    assert isinstance(schedule, SimpleSchedule)
    day_len = _window_len_seconds(schedule.morning_time, schedule.night_time)
    night_len = _window_len_seconds(schedule.night_time, schedule.morning_time)
    if day_len <= 0:
        return "morning_time must be before night_time on the same day"
    if schedule.pulse_seconds * schedule.day_pulse_count > day_len:
        return "day pulses do not fit in the day window (reduce count or pulse seconds)"
    if schedule.pulse_seconds * schedule.night_pulse_count > night_len:
        return "night pulses do not fit in the night window (reduce count or pulse seconds)"
    return None


def _at_local(day: date, hhmm: str, tz: ZoneInfo) -> datetime:
    h, m = _parse_hhmm(hhmm)
    return datetime(day.year, day.month, day.day, h, m, 0, tzinfo=tz)


def _even_starts(start: datetime, end: datetime, count: int) -> list[datetime]:
    span = (end - start).total_seconds()
    if span <= 0 or count < 1:
        return []
    return [start + timedelta(seconds=i * (span / count)) for i in range(count)]


def simple_windows_for_date(
    schedule: SimpleSchedule, day: date, tz: ZoneInfo
) -> list[tuple[datetime, datetime]]:
    pulse = timedelta(seconds=schedule.pulse_seconds)
    morning = _at_local(day, schedule.morning_time, tz)
    night = _at_local(day, schedule.night_time, tz)
    next_morning = _at_local(day + timedelta(days=1), schedule.morning_time, tz)

    windows: list[tuple[datetime, datetime]] = []
    for start in _even_starts(morning, night, schedule.day_pulse_count):
        windows.append((start, start + pulse))
    for start in _even_starts(night, next_morning, schedule.night_pulse_count):
        windows.append((start, start + pulse))
    return windows


def advanced_windows_for_date(
    schedule: AdvancedSchedule, day: date, tz: ZoneInfo
) -> list[tuple[datetime, datetime]]:
    pulse = timedelta(seconds=schedule.pulse_seconds)
    windows: list[tuple[datetime, datetime]] = []
    for hhmm in schedule.times:
        start = _at_local(day, hhmm, tz)
        windows.append((start, start + pulse))
    windows.sort(key=lambda w: w[0])
    return windows


def collect_windows(
    schedule_type: str,
    schedule: dict[str, Any],
    center: datetime,
    tz: ZoneInfo,
) -> list[tuple[datetime, datetime]]:
    days = [center.date() + timedelta(days=d) for d in (-1, 0, 1)]
    windows: list[tuple[datetime, datetime]] = []
    if schedule_type == "simple":
        model = SimpleSchedule.model_validate(schedule)
        for day in days:
            windows.extend(simple_windows_for_date(model, day, tz))
    else:
        model = AdvancedSchedule.model_validate(schedule)
        for day in days:
            windows.extend(advanced_windows_for_date(model, day, tz))
    return sorted(windows, key=lambda w: w[0])


def runtime_from_schedule(
    schedule_type: str,
    schedule: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    tz = get_tz()
    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc).astimezone(tz)
    else:
        now = now.astimezone(tz)

    windows = collect_windows(schedule_type, schedule, now, tz)
    for start, end in windows:
        if start <= now < end:
            return {
                "in_on_phase": True,
                "seconds_until_change": max(0, int((end - now).total_seconds())),
                "seconds_until_activation": max(0, int((end - now).total_seconds())),
            }

    future_starts = [start for start, _end in windows if start > now]
    if future_starts:
        nxt = min(future_starts)
        return {
            "in_on_phase": False,
            "seconds_until_change": max(0, int((nxt - now).total_seconds())),
            "seconds_until_activation": max(0, int((nxt - now).total_seconds())),
        }

    return {
        "in_on_phase": False,
        "seconds_until_change": None,
        "seconds_until_activation": None,
    }
