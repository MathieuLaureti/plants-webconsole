"""Multi-plug schedule engine."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import database.kasa_plugs as plugs_db
from kasa_control import client as kasa_client
from kasa_control import config as kasa_config
from kasa_control.schedule_compute import get_tz, runtime_from_schedule

logger = logging.getLogger(__name__)

TICK_SECONDS = 1.0


@dataclass
class PlugRuntime:
    last_applied_on: bool | None = None
    last_error: str | None = None


@dataclass
class EngineState:
    task: asyncio.Task | None = None
    runtimes: dict[int, PlugRuntime] = field(default_factory=dict)


_state = EngineState()
_lock = asyncio.Lock()


def _runtime_for_plug(plug_id: int) -> PlugRuntime:
    if plug_id not in _state.runtimes:
        _state.runtimes[plug_id] = PlugRuntime()
    return _state.runtimes[plug_id]


def want_power_on(plug: dict[str, Any], now: datetime | None = None) -> bool:
    rt = runtime_from_schedule(plug["schedule_type"], plug["schedule"], now)
    return bool(rt["in_on_phase"])


async def get_plug_runtime(plug_id: int) -> dict[str, Any]:
    plug = plugs_db.fetch_plug(plug_id)
    if plug is None:
        return {"found": False}

    configured = kasa_config.is_configured()
    runtime = _runtime_for_plug(plug_id)
    schedule_rt = runtime_from_schedule(plug["schedule_type"], plug["schedule"])

    plug_on: bool | None = runtime.last_applied_on
    if configured:
        try:
            plug_on = await kasa_client.get_state(plug["host"])
            runtime.last_applied_on = plug_on
            runtime.last_error = None
        except Exception as exc:
            runtime.last_error = str(exc)

    return {
        "found": True,
        "id": plug_id,
        "configured": configured,
        "schedule_enabled": plug["schedule_enabled"],
        "plug_on": plug_on,
        "in_on_phase": schedule_rt["in_on_phase"] if plug["schedule_enabled"] else False,
        "seconds_until_change": schedule_rt["seconds_until_change"]
        if plug["schedule_enabled"]
        else None,
        "error": runtime.last_error,
    }


async def disable_plug_power(plug: dict[str, Any]) -> None:
    await _disable_plug_power(plug)


async def _apply_plug(plug: dict[str, Any]) -> None:
    plug_id = plug["id"]
    runtime = _runtime_for_plug(plug_id)
    tz = get_tz()
    now = datetime.now(tz)
    target_on = want_power_on(plug, now)
    if runtime.last_applied_on is not None and runtime.last_applied_on == target_on:
        return
    try:
        applied = await kasa_client.set_power(plug["host"], target_on)
        runtime.last_applied_on = applied
        runtime.last_error = None
    except Exception as exc:
        logger.warning("Kasa error plug %s (%s): %s", plug_id, plug["host"], exc)
        runtime.last_error = str(exc)


async def _disable_plug_power(plug: dict[str, Any]) -> None:
    runtime = _runtime_for_plug(plug["id"])
    try:
        await kasa_client.set_power(plug["host"], False)
        runtime.last_applied_on = False
        runtime.last_error = None
    except Exception as exc:
        runtime.last_error = str(exc)


async def _tick() -> None:
    while True:
        wait = TICK_SECONDS
        try:
            if not kasa_config.is_configured():
                await asyncio.sleep(TICK_SECONDS)
                continue

            enabled = plugs_db.fetch_enabled_plugs()
            enabled_ids = {p["id"] for p in enabled}

            async with _lock:
                stale = [pid for pid in _state.runtimes if pid not in enabled_ids]
            for pid in stale:
                plug = plugs_db.fetch_plug(pid)
                if plug and not plug["schedule_enabled"]:
                    await _disable_plug_power(plug)

            for plug in enabled:
                await _apply_plug(plug)
                await asyncio.sleep(0.15)

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Plug scheduler tick failed: %s", exc)
        await asyncio.sleep(wait)


async def start() -> None:
    async with _lock:
        if _state.task is None or _state.task.done():
            _state.task = asyncio.create_task(_tick(), name="multi_plug_schedule")


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
