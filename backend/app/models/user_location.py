from datetime import datetime
from typing import Optional

from sqlalchemy import Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BigIntPK, TimestampMixin
from app.database.session import Base


class UserLocation(Base, TimestampMixin):
    __tablename__ = "user_locations"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigIntPK, index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    heading: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tracked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
