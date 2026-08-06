from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Rating
from app.repositories.base import BaseRepository


class RatingRepository(BaseRepository[Rating, None, None]):
    def __init__(self, db: Session):
        super().__init__(Rating, db)

    def get_by_user_and_dest(self, user_id: int, destination_id: int) -> Optional[Rating]:
        return self.get_by(user_id=user_id, destination_id=destination_id)

    def list_for_destination(self, destination_id: int, page: int, per_page: int) -> tuple[list[Rating], int]:
        total = int(
            self.db.scalar(
                select(func.count(Rating.id)).where(Rating.destination_id == destination_id)
            )
            or 0
        )
        stmt = (
            select(Rating)
            .where(Rating.destination_id == destination_id)
            .order_by(Rating.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(self.db.scalars(stmt).all()), total
