from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from auth.config import validate_auth_config
from config import BASE_DIR
import database
from kasa_control import scheduler as plug_scheduler
from routes import register_routes
from upload_storage import ensure_upload_root

ensure_upload_root()
database.init_captures_db()
validate_auth_config()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await plug_scheduler.start()
    yield
    await plug_scheduler.stop()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=BASE_DIR), name="uploads")
register_routes(app)
