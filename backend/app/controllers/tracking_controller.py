from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.tracking_repository import SearchHistoryRepository, UserLocationRepository
from app.schemas.location import LocationUpdate
from app.schemas.search import SavedSearch
from app.services.map_service import get_route
from app.services.weather_service import get_weather


def save_search(db: Session, user: User, payload: SavedSearch) -> dict:
    repo = SearchHistoryRepository(db)
    row = repo.create_raw(
        user_id=user.id,
        query=payload.query[:255] if payload.query else None,
        filters=payload.filters,
        result_count=payload.result_count,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.commit()
    return {"history": {"id": row.id, "query": row.query, "created_at": row.created_at}}


def list_history(db: Session, user: User, limit: int) -> dict:
    repo = SearchHistoryRepository(db)
    rows = repo.list_by_user(user.id, limit)
    return {
        "data": [
            {
                "id": r.id,
                "query": r.query,
                "filters": r.filters,
                "result_count": r.result_count,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


def delete_history(db: Session, user: User, history_id: Optional[int]) -> dict:
    repo = SearchHistoryRepository(db)
    repo.delete_for_user(user.id, history_id)
    db.commit()
    return {"message": "Riwayat dihapus"}


def update_location(db: Session, user: User, payload: LocationUpdate, request: Request) -> dict:
    repo = UserLocationRepository(db)
    row = repo.create_raw(
        user_id=user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        speed=payload.speed,
        heading=payload.heading,
        tracked_at=datetime.now(timezone.utc),
    )
    db.commit()
    return {"message": "Lokasi diperbarui", "tracked_at": row.tracked_at.isoformat()}


def get_latest_location(db: Session, user: User) -> dict:
    repo = UserLocationRepository(db)
    row = repo.latest_for_user(user.id)
    if not row:
        return {"latitude": None, "longitude": None, "accuracy": None}
    return {
        "latitude": row.latitude,
        "longitude": row.longitude,
        "accuracy": row.accuracy,
        "tracked_at": row.tracked_at.isoformat(),
    }
