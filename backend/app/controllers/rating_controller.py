from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import Destination, User
from app.repositories.destination_repository import DestinationRepository
from app.repositories.rating_repository import RatingRepository
from app.schemas.misc import RatingCreate


def list_ratings(db: Session, destination_id: int, page: int, per_page: int) -> dict:
    DestinationRepository(db).get(destination_id) or _not_found()
    rows, total = RatingRepository(db).list_for_destination(destination_id, page, per_page)
    pages = max(1, (total + per_page - 1) // per_page)
    return {
        "data": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "username": r.user.username if r.user else None,
                "score": r.score,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
    }


def add_rating(db: Session, user: User, destination_id: int, payload: RatingCreate) -> dict:
    if payload.score is None or not (1 <= payload.score <= 5):
        raise BadRequestError("Skor rating harus antara 1 dan 5", "INVALID_RATING")
    if not DestinationRepository(db).get(destination_id):
        _not_found()

    repo = RatingRepository(db)
    existing = repo.get_by_user_and_dest(user.id, destination_id)
    if existing:
        existing.score = payload.score
        existing.comment = payload.comment or existing.comment
        db.commit()
        db.refresh(existing)
        return {"rating": _serialize(existing), "updated": True}

    rating = repo.create_raw(
        user_id=user.id,
        destination_id=destination_id,
        score=payload.score,
        comment=payload.comment,
    )
    db.commit()
    db.refresh(rating)
    return {"rating": _serialize(rating), "updated": False}


def _serialize(r: object) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "username": r.user.username if r.user else None,
        "score": r.score,
        "comment": r.comment,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _not_found():
    raise NotFoundError("Destinasi tidak ditemukan", "DESTINATION_NOT_FOUND")
