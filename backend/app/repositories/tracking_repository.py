from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RefreshToken, SearchHistory, UserLocation
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken, None, None]):
    def __init__(self, db: Session):
        super().__init__(RefreshToken, db)

    def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        return self.get_by(token_hash=token_hash)

    def revoke(self, token: RefreshToken) -> None:
        from datetime import datetime, timezone

        token.revoked_at = datetime.now(timezone.utc)

    def revoke_all_for_user(self, user_id: int) -> None:
        from datetime import datetime, timezone

        tokens = list(self.db.scalars(select(RefreshToken).where(RefreshToken.user_id == user_id)))
        for t in tokens:
            if not t.revoked_at:
                t.revoked_at = datetime.now(timezone.utc)


class SearchHistoryRepository(BaseRepository[SearchHistory, None, None]):
    def __init__(self, db: Session):
        super().__init__(SearchHistory, db)

    def list_by_user(self, user_id: int, limit: int = 20) -> list[SearchHistory]:
        stmt = (
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def delete_for_user(self, user_id: int, history_id: Optional[int] = None) -> int:
        stmt = SearchHistory.__table__.delete().where(SearchHistory.user_id == user_id)
        if history_id:
            stmt = stmt.where(SearchHistory.id == history_id)
        result = self.db.execute(stmt)
        return result.rowcount or 0


class UserLocationRepository(BaseRepository[UserLocation, None, None]):
    def __init__(self, db: Session):
        super().__init__(UserLocation, db)

    def latest_for_user(self, user_id: int) -> Optional[UserLocation]:
        stmt = (
            select(UserLocation)
            .where(UserLocation.user_id == user_id)
            .order_by(UserLocation.tracked_at.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()
