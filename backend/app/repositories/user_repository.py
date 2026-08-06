from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.base import BaseRepository
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserUpdate


class UserRepository(BaseRepository[User, RegisterRequest, UserUpdate]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.get_by(email=email.lower())

    def get_by_username(self, username: str) -> Optional[User]:
        return self.get_by(username=username)

    def get_by_identifier(self, identifier: str) -> Optional[User]:
        identifier = identifier.strip().lower()
        stmt = select(User).where((User.email == identifier) | (User.username == identifier))
        return self.db.scalars(stmt).first()

    def list_paginated(self, page: int, per_page: int, role: Optional[str] = None, query: Optional[str] = None):
        conditions = []
        if role:
            conditions.append(User.role == role)
        if query:
            like = f"%{query.lower()}%"
            conditions.append(
                (User.email.ilike(like)) | (User.username.ilike(like)) | (User.full_name.ilike(like))
            )

        count_stmt = select(func.count(User.id))
        for cond in conditions:
            count_stmt = count_stmt.where(cond)
        total = int(self.db.scalar(count_stmt) or 0)

        stmt = select(User)
        for cond in conditions:
            stmt = stmt.where(cond)
        stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        return list(self.db.scalars(stmt).all()), total
