from fastapi import FastAPI

from auth.routes import router as auth_router
from routes.health import router as health_router
from routes.images import router as images_router
from routes.plug import router as plug_router
from routes.sensors import router as sensors_router
from routes.timelapse import router as timelapse_router
from routes.upload import router as upload_router


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(upload_router)
    app.include_router(images_router)
    app.include_router(sensors_router)
    app.include_router(timelapse_router)
    app.include_router(plug_router)
