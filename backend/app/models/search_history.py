from typing import Optional

from sqlalchemy import Float, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BigIntPK, TimestampMixin
from app.database.session import Base

JSONB = JSON().with_variant(postgresql.JSONB(), "postgresql")


class SearchHistory(Base, TimestampMixin):
    __tablename__ = "search_histories"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, index=True, nullable=False
    )
    query: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
