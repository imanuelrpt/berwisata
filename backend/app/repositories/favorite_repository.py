from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Favorite
from app.repositories.base import BaseRepository
from app.schemas.misc import FavoriteCreate


class FavoriteRepository(BaseRepository[Favorite, FavoriteCreate, FavoriteCreate]):
    def __init__(self, db: Session):
        super().__init__(Favorite, db)

    def get_by_user_and_dest(self, user_id: int, destination_id: int) -> Optional[Favorite]:
        return self.get_by(user_id=user_id, destination_id=destination_id)

    def list_by_user(self, user_id: int, page: int, per_page: int) -> tuple[list[Favorite], int]:
        total = int(
            self.db.scalar(select(func.count(Favorite.id)).where(Favorite.user_id == user_id)) or 0
        )
        stmt = (
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(self.db.scalars(stmt).all()), total

    def ids_by_user(self, user_id: int) -> list[int]:
        stmt = select(Favorite.destination_id).where(Favorite.user_id == user_id)
        return list(self.db.scalars(stmt).all())
