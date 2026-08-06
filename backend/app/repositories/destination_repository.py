from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Destination, DestinationImage
from app.repositories.base import BaseRepository
from app.schemas.destination import DestinationCreate, DestinationUpdate


class DestinationRepository(BaseRepository[Destination, DestinationCreate, DestinationUpdate]):
    def __init__(self, db: Session):
        super().__init__(Destination, db)

    def get_by_slug(self, slug: str) -> Optional[Destination]:
        return self.get_by(slug=slug)

    def get_with_images(self, obj_id: int) -> Optional[Destination]:
        stmt = (
            select(Destination)
            .options()
            .where(Destination.id == obj_id)
        )
        return self.db.scalars(stmt).first()

    def list_paginated(self, page: int, per_page: int, **filters) -> tuple[list[Destination], int]:
        conditions = []
        for k, v in filters.items():
            if v is not None:
                conditions.append(getattr(Destination, k) == v)

        count_stmt = select(func.count(Destination.id))
        for cond in conditions:
            count_stmt = count_stmt.where(cond)
        total = int(self.db.scalar(count_stmt) or 0)

        stmt = select(Destination)
        for cond in conditions:
            stmt = stmt.where(cond)
        stmt = stmt.order_by(Destination.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        return list(self.db.scalars(stmt).all()), total

    def add_image(self, destination_id: int, url: str, caption: Optional[str], is_primary: bool, sort_order: int) -> DestinationImage:
        img = DestinationImage(
            destination_id=destination_id,
            url=url,
            caption=caption,
            is_primary=is_primary,
            sort_order=sort_order,
        )
        self.db.add(img)
        return img

    def remove_image(self, image_id: int) -> bool:
        img = self.db.get(DestinationImage, image_id)
        if img is None:
            return False
        self.db.delete(img)
        return True

    def set_primary_image(self, destination_id: int, image_id: int) -> None:
        self.db.execute(
            DestinationImage.__table__.update()
            .where(DestinationImage.destination_id == destination_id)
            .values(is_primary=False)
        )
        img = self.db.get(DestinationImage, image_id)
        if img:
            img.is_primary = True

    def increment_views(self, obj: Destination, by: int = 1) -> None:
        obj.view_count += by

    def get_trending(self, limit: int = 10) -> list[Destination]:
        stmt = (
            select(Destination)
            .where(Destination.is_trending.is_(True))
            .order_by(Destination.popularity.desc(), Destination.hidden_gem_score.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_featured(self, limit: int = 10) -> list[Destination]:
        stmt = (
            select(Destination)
            .where(Destination.is_featured.is_(True))
            .order_by(Destination.hidden_gem_score.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
