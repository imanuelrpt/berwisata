from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import User
from app.repositories.favorite_repository import FavoriteRepository
from app.schemas.misc import FavoriteCreate
from app.services import destination_service
from app.services.map_service import get_route


def list_favorites(db: Session, user: User, page: int, per_page: int) -> dict:
    repo = FavoriteRepository(db)
    favorites, total = repo.list_by_user(user.id, page, per_page)
    data = []
    for fav in favorites:
        dest = fav.destination
        if dest:
            item = destination_service.serialize_destination(dest)
            item["is_favorited"] = True
            data.append(item)
    return {"data": data, "meta": _meta(page, per_page, total)}


def add_favorite(db: Session, user: User, payload: FavoriteCreate) -> dict:
    repo = FavoriteRepository(db)
    dest = destination_service.get_destination_or_404(db, payload.destination_id)
    if repo.get_by_user_and_dest(user.id, payload.destination_id):
        raise BadRequestError("Destinasi sudah masuk favorit", "ALREADY_FAVORITED")
    fav = repo.create_raw(user_id=user.id, destination_id=payload.destination_id)
    db.commit()
    return {"favorited": True, "destination_id": payload.destination_id, "name": dest.name}


def remove_favorite(db: Session, user: User, destination_id: int) -> dict:
    repo = FavoriteRepository(db)
    fav = repo.get_by_user_and_dest(user.id, destination_id)
    if not fav:
        raise NotFoundError("Destinasi tidak ada di favorit", "NOT_FAVORITED")
    repo.delete(fav)
    return {"favorited": False, "destination_id": destination_id}


def _meta(page: int, per_page: int, total: int) -> dict:
    pages = max(1, (total + per_page - 1) // per_page)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
