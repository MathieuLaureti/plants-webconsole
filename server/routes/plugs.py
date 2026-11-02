from fastapi import APIRouter, Depends, HTTPException

import database.kasa_plugs as plugs_db
from auth.deps import get_current_user
from kasa_control import config as kasa_config
from kasa_control import scheduler as plug_scheduler
from kasa_control.plug_models import (
    PlugCreate,
    PlugUpdate,
    ScheduleEnabledUpdate,
    validate_schedule_for_type,
)
from kasa_control.schedule_compute import validate_schedule_capacity

router = APIRouter(prefix="/plugs", tags=["plugs"])


def _require_kasa() -> None:
    if not kasa_config.is_configured():
        raise HTTPException(
            status_code=503,
            detail="KASA_USERNAME and KASA_PASSWORD must be configured",
        )


def _schedule_body(body: PlugCreate) -> dict:
    schedule = validate_schedule_for_type(body.schedule_type, body.schedule)
    err = validate_schedule_capacity(body.schedule_type, schedule)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return schedule.model_dump()


@router.get("")
async def list_plugs(_user: str = Depends(get_current_user)):
    return plugs_db.list_plugs()


@router.post("")
async def create_plug(body: PlugCreate, _user: str = Depends(get_current_user)):
    _require_kasa()
    schedule = _schedule_body(body)
    try:
        return plugs_db.insert_plug(
            host=body.host,
            title=body.title,
            description=body.description,
            schedule_type=body.schedule_type,
            schedule=schedule,
        )
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(status_code=409, detail="host already registered") from exc
        raise


@router.get("/{plug_id}")
async def get_plug(plug_id: int, _user: str = Depends(get_current_user)):
    plug = plugs_db.fetch_plug(plug_id)
    if plug is None:
        raise HTTPException(status_code=404, detail="plug not found")
    return plug


@router.put("/{plug_id}")
async def update_plug(
    plug_id: int, body: PlugUpdate, _user: str = Depends(get_current_user)
):
    _require_kasa()
    existing = plugs_db.fetch_plug(plug_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="plug not found")

    schedule_type = body.schedule_type or existing["schedule_type"]
    if body.schedule is not None:
        schedule = validate_schedule_for_type(schedule_type, body.schedule)
        err = validate_schedule_capacity(schedule_type, schedule)
        if err:
            raise HTTPException(status_code=400, detail=err)
        schedule_dict = schedule.model_dump()
    else:
        schedule_dict = None

    try:
        updated = plugs_db.update_plug(
            plug_id,
            host=body.host,
            title=body.title,
            description=body.description,
            schedule_type=body.schedule_type,
            schedule=schedule_dict,
        )
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(status_code=409, detail="host already registered") from exc
        raise
    return updated


@router.delete("/{plug_id}")
async def remove_plug(plug_id: int, _user: str = Depends(get_current_user)):
    existing = plugs_db.fetch_plug(plug_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="plug not found")
    if existing["schedule_enabled"]:
        await plug_scheduler.disable_plug_power(existing)
    if not plugs_db.delete_plug(plug_id):
        raise HTTPException(status_code=404, detail="plug not found")
    return {"deleted": True, "id": plug_id}


@router.put("/{plug_id}/schedule/enabled")
async def set_schedule_enabled(
    plug_id: int,
    body: ScheduleEnabledUpdate,
    _user: str = Depends(get_current_user),
):
    _require_kasa()
    existing = plugs_db.fetch_plug(plug_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="plug not found")
    updated = plugs_db.set_schedule_enabled(plug_id, body.enabled)
    if not body.enabled:
        await plug_scheduler.disable_plug_power(existing)
    return updated


@router.get("/{plug_id}/runtime")
async def plug_runtime(plug_id: int, _user: str = Depends(get_current_user)):
    result = await plug_scheduler.get_plug_runtime(plug_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail="plug not found")
    return result
