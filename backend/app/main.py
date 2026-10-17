import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import analyze, health, jobs
from app.config import get_settings
from app.db import JobStore
from app.rules.catalog import load_catalog
from app.worker import worker_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if not settings.api_keys:
        raise RuntimeError("Set API_KEYS before starting the service")
    app.state.rules = load_catalog(settings.rules_path)
    app.state.store = JobStore(settings.db_path)
    app.state.store.recover()
    stop = threading.Event()
    thread = None
    if os.getenv("WORKER_ENABLED", "true").lower() in {"1", "true", "yes"}:
        thread = threading.Thread(target=worker_loop, args=(app.state.store, stop), daemon=True, name="video-worker")
        thread.start()
    app.state.worker_stop = stop
    app.state.worker_thread = thread
    yield
    stop.set()
    if thread is not None:
        thread.join(timeout=5)


app = FastAPI(title="Local Video Analysis API", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Invalid request"})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Unhandled request error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
