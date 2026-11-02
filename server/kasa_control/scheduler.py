"""Background pulse schedule for the Kasa plug (runs without the browser open)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from kasa_control import client as kasa_client
from kasa_control import config as kasa_config

logger = logging.getLogger(__name__)

SCHEDULE_PATH = os.environ.get(
    "PLUG_SCHEDULE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "plug_schedule.json"),
)

TICK_SECONDS = 1.0


@dataclass
class ScheduleConfig:
    enabled: bool = False
    interval_minutes: int = 5
    on_minutes: int = 1
    cycle_started_at: float | None = None  # unix seconds UTC

    def wait_seconds(self) -> int:
        """Minutes power stays OFF between activations."""
        return max(1, self.interval_minutes) * 60

    def on_seconds(self) -> int:
        return max(1, self.on_minutes) * 60

    def cycle_seconds(self) -> int:
        return self.wait_seconds() + self.on_seconds()

    def validate(self) -> str | None:
        if self.interval_minutes < 1:
            return "wait_minutes must be at least 1"
        if self.on_minutes < 1:
            return "on_minutes must be at least 1"
        return None

    def _phase(self, now: float) -> float:
        elapsed = now - self.cycle_started_at  # type: ignore[operator]
        if elapsed < 0:
            elapsed = 0
        return elapsed % self.cycle_seconds()

    def want_power_on(self, now: float) -> bool:
        if not self.enabled or self.cycle_started_at is None:
            return False
        return self._phase(now) >= self.wait_seconds()

    def seconds_until_next_change(self, now: float) -> float:
        if not self.enabled or self.cycle_started_at is None:
            return TICK_SECONDS
        phase = self._phase(now)
        wait = self.wait_seconds()
        cycle = self.cycle_seconds()
        if phase < wait:
            return max(0.5, wait - phase)
        return max(0.5, cycle - phase)

    def seconds_until_activation(self, now: float) -> float:
        """Seconds until the plug turns ON (start of ON phase)."""
        if not self.enabled or self.cycle_started_at is None:
            return TICK_SECONDS
        phase = self._phase(now)
        wait = self.wait_seconds()
        cycle = self.cycle_seconds()
        if phase < wait:
            return max(0.5, wait - phase)
        return max(0.5, cycle - phase + wait)


@dataclass
class SchedulerState:
    config: ScheduleConfig = field(default_factory=ScheduleConfig)
    task: asyncio.Task | None = None
    last_applied_on: bool | None = None
    last_error: str | None = None


_state = SchedulerState()
_lock = asyncio.Lock()


def _load_config() -> ScheduleConfig:
    path = os.path.abspath(SCHEDULE_PATH)
    if not os.path.isfile(path):
        return ScheduleConfig()
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        cfg = ScheduleConfig(
            enabled=bool(raw.get("enabled", False)),
            interval_minutes=int(raw.get("interval_minutes", 5)),
            on_minutes=int(raw.get("on_minutes", 1)),
            cycle_started_at=raw.get("cycle_started_at"),
        )
        if cfg.validate() is not None:
            cfg.enabled = False
        return cfg
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Could not load plug schedule: %s", exc)
        return ScheduleConfig()


def _save_config(cfg: ScheduleConfig) -> None:
    path = os.path.abspath(SCHEDULE_PATH)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    payload = asdict(cfg)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    os.replace(tmp, path)


def _public_status(cfg: ScheduleConfig, plug_on: bool | None) -> dict[str, Any]:
    now = datetime.now(timezone.utc).timestamp()
    err = cfg.validate() if cfg.enabled else None
    return {
        "enabled": cfg.enabled and err is None,
        "interval_minutes": cfg.interval_minutes,
        "on_minutes": cfg.on_minutes,
        "configured": kasa_config.is_configured(),
        "plug_on": plug_on,
        "in_on_phase": cfg.want_power_on(now) if cfg.enabled and err is None else False,
        "seconds_until_change": int(cfg.seconds_until_next_change(now))
        if cfg.enabled and err is None
        else None,
        "seconds_until_activation": int(cfg.seconds_until_activation(now))
        if cfg.enabled and err is None
        else None,
        "cycle_minutes": cfg.interval_minutes + cfg.on_minutes,
        "error": err or _state.last_error,
    }


async def get_status() -> dict[str, Any]:
    async with _lock:
        cfg = _state.config
        plug_on = _state.last_applied_on
    if kasa_config.is_configured():
        try:
            plug_on = await kasa_client.get_state()
            async with _lock:
                _state.last_applied_on = plug_on
                _state.last_error = None
        except Exception as exc:
            async with _lock:
                _state.last_error = str(exc)
    async with _lock:
        return _public_status(_state.config, plug_on)


async def apply_schedule(
    *,
    enabled: bool | None = None,
    interval_minutes: int | None = None,
    on_minutes: int | None = None,
) -> dict[str, Any]:
    async with _lock:
        prev = _state.config
        cfg = ScheduleConfig(
            enabled=prev.enabled if enabled is None else enabled,
            interval_minutes=interval_minutes
            if interval_minutes is not None
            else prev.interval_minutes,
            on_minutes=on_minutes if on_minutes is not None else prev.on_minutes,
            cycle_started_at=prev.cycle_started_at,
        )
        timing_changed = (
            interval_minutes is not None and interval_minutes != prev.interval_minutes
        ) or (on_minutes is not None and on_minutes != prev.on_minutes)
        if enabled is False:
            cfg.enabled = False
            cfg.cycle_started_at = None
        elif cfg.enabled and (
            enabled is True or timing_changed or cfg.cycle_started_at is None
        ):
            cfg.cycle_started_at = datetime.now(timezone.utc).timestamp()
        err = cfg.validate() if cfg.enabled else None
        if err:
            raise ValueError(err)
        _state.config = cfg
        _save_config(cfg)

    if not cfg.enabled and kasa_config.is_configured():
        try:
            await kasa_client.set_power(False)
            async with _lock:
                _state.last_applied_on = False
        except Exception as exc:
            async with _lock:
                _state.last_error = str(exc)

    return await get_status()


async def _tick() -> None:
    while True:
        try:
            if not kasa_config.is_configured():
                await asyncio.sleep(TICK_SECONDS)
                continue
            async with _lock:
                cfg = _state.config
                if not cfg.enabled:
                    await asyncio.sleep(TICK_SECONDS)
                    continue
                if cfg.validate():
                    cfg.enabled = False
                    cfg.cycle_started_at = None
                    _save_config(cfg)
                    continue
                now = datetime.now(timezone.utc).timestamp()
                want_on = cfg.want_power_on(now)
                last = _state.last_applied_on
            if last is None or want_on != last:
                try:
                    applied = await kasa_client.set_power(want_on)
                    async with _lock:
                        _state.last_applied_on = applied
                        _state.last_error = None
                except Exception as exc:
                    logger.warning("Plug schedule kasa error: %s", exc)
                    async with _lock:
                        _state.last_error = str(exc)
            async with _lock:
                wait = _state.config.seconds_until_next_change(
                    datetime.now(timezone.utc).timestamp()
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Plug schedule tick failed: %s", exc)
            wait = TICK_SECONDS
        await asyncio.sleep(min(TICK_SECONDS, wait))


async def start() -> None:
    async with _lock:
        _state.config = _load_config()
        if _state.config.enabled and _state.config.cycle_started_at is None:
            _state.config.cycle_started_at = datetime.now(timezone.utc).timestamp()
            _save_config(_state.config)
        if _state.task is None or _state.task.done():
            _state.task = asyncio.create_task(_tick(), name="plug_schedule")


async def stop() -> None:
    async with _lock:
        task = _state.task
        _state.task = None
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
