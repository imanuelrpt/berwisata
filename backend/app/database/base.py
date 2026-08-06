from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base

# Auto-incrementing primary key type: BIGINT on PostgreSQL, INTEGER on SQLite
# (SQLite only autoincrements for "INTEGER PRIMARY KEY").
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
