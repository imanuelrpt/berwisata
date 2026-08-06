from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.database.session import engine
from app.services.ml_service import model_available, training_metadata

router = APIRouter(tags=["System"])


@router.get("/health")
def health():
    db_status = "down"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "up"
    except Exception:
        db_status = "down"
    return {
        "status": "ok" if db_status == "up" else "degraded",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
        "ml_model": "ready" if model_available() else "not_loaded",
        "ml_metadata": training_metadata(),
        "time": datetime.now(timezone.utc).isoformat(),
    }
