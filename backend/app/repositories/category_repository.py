from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, Destination
from app.repositories.base import BaseRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryRepository(BaseRepository[Category, CategoryCreate, CategoryUpdate]):
    def __init__(self, db: Session):
        super().__init__(Category, db)

    def get_by_slug(self, slug: str) -> Optional[Category]:
        return self.get_by(slug=slug)

    def list_with_counts(self) -> list[tuple[Category, int]]:
        stmt = (
            select(Category, func.count(Destination.id).label("dest_count"))
            .outerjoin(Destination, Destination.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.sort_order.asc(), Category.name.asc())
        )
        return list(self.db.execute(stmt).all())
