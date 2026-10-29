from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from auth.deps import get_current_user
from kasa_control import client as kasa_client
from kasa_control import config as kasa_config
from kasa_control.errors import friendly_kasa_error

router = APIRouter(prefix="/plug", tags=["plug"])


def _kasa_error_response(exc: BaseException) -> JSONResponse | None:
    hint = friendly_kasa_error(exc)
    if hint:
        return JSONResponse(
            content={"configured": True, "on": None, "error": hint},
        )
    return None


@router.get("/state")
async def plug_state(_user: str = Depends(get_current_user)):
    if not kasa_config.is_configured():
        return JSONResponse(
            content={"configured": False, "on": None, "error": "KASA_* not configured"},
        )
    try:
        on = await kasa_client.get_state()
        return {"configured": True, "on": on, "error": None}
    except Exception as exc:
        response = _kasa_error_response(exc)
        if response is not None:
            return response
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/on")
async def plug_on(_user: str = Depends(get_current_user)):
    if not kasa_config.is_configured():
        raise HTTPException(status_code=503, detail="KASA_* not configured")
    try:
        on = await kasa_client.set_power(True)
        return {"configured": True, "on": on, "error": None}
    except Exception as exc:
        response = _kasa_error_response(exc)
        if response is not None:
            return response
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/off")
async def plug_off(_user: str = Depends(get_current_user)):
    if not kasa_config.is_configured():
        raise HTTPException(status_code=503, detail="KASA_* not configured")
    try:
        on = await kasa_client.set_power(False)
        return {"configured": True, "on": on, "error": None}
    except Exception as exc:
        response = _kasa_error_response(exc)
        if response is not None:
            return response
        raise HTTPException(status_code=502, detail=str(exc)) from exc
