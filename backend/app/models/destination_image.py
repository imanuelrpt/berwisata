from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BigIntPK, TimestampMixin
from app.database.session import Base


class DestinationImage(Base, TimestampMixin):
    __tablename__ = "destination_images"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    destination_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("destinations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    destination = relationship("Destination", back_populates="images")
