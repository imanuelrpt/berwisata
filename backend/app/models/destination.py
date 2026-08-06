from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BigIntPK, TimestampMixin
from app.database.session import Base

JSONB = JSON().with_variant(postgresql.JSONB(), "postgresql")


class Destination(Base, TimestampMixin):
    __tablename__ = "destinations"
    __table_args__ = (
        Index("ix_destinations_geo", "latitude", "longitude"),
        Index("ix_destinations_province", "province"),
        Index("ix_destinations_regency", "regency"),
        Index("ix_destinations_rating", "rating"),
        Index("ix_destinations_score", "hidden_gem_score"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    category_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    regency: Mapped[str] = mapped_column(String(120), nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    village: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    price_min: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    price_max: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="IDR", nullable=False)

    opening_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "06:00"
    closing_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "18:00"
    is_open_24h: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    days_open: Mapped[list] = mapped_column(JSONB, default=lambda: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])

    rating: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    popularity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # weekly popularity index
    visitor_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # est. visitors/year

    facilities: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # ["parkir","wc",...]

    # ML input features
    safety: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)        # 1-5
    cleanliness: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)   # 1-5
    beauty: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)        # 1-5
    road_access: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)   # 1-5
    crowd_level: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)   # 1-5 (5 = sangat ramai)

    hidden_gem_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    instagram: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category = relationship("Category", lazy="joined")
    images = relationship(
        "DestinationImage", back_populates="destination", cascade="all, delete-orphan", order_by="DestinationImage.sort_order"
    )
    favorites = relationship("Favorite", back_populates="destination", cascade="all, delete-orphan")
