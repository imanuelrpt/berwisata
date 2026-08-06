"""BerWisata FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging

logger = logging.getLogger("app.main")

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_GLOBAL])


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.DEBUG)
    Path(settings.upload_path).mkdir(parents=True, exist_ok=True)
    Path(settings.ML_MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.APP_ENV)

    if settings.ML_USE_CACHED_MODEL:
        try:
            from app.services import ml_service

            ml_service.reload_model()
        except Exception as exc:  # pragma: no cover
            logger.warning("ML model init skipped: %s", exc)

    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="REST API untuk platform pencarian & rekomendasi destinasi wisata hidden gem di Indonesia.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
