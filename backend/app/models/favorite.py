from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BigIntPK, TimestampMixin
from app.database.session import Base


class Favorite(Base, TimestampMixin):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "destination_id", name="uq_favorite_user_destination"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("destinations.id", ondelete="CASCADE"), index=True, nullable=False
    )

    destination = relationship("Destination", back_populates="favorites")
