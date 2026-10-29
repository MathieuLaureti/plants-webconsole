from fastapi import FastAPI

from routes.health import router as health_router
from routes.images import router as images_router
from routes.sensors import router as sensors_router
from routes.timelapse import router as timelapse_router
from routes.upload import router as upload_router


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router)
    app.include_router(upload_router)
    app.include_router(images_router)
    app.include_router(sensors_router)
    app.include_router(timelapse_router)
