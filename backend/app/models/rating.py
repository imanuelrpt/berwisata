from sqlalchemy import Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BigIntPK, TimestampMixin
from app.database.session import Base


class Rating(Base, TimestampMixin):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("user_id", "destination_id", name="uq_rating_user_destination"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("destinations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 1-5
    comment: Mapped[str] = mapped_column(Text, default="", nullable=True)

    user = relationship("User", lazy="joined")
