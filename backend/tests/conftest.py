"""Shared pytest fixtures.

Configures an in-memory SQLite database before any application module import,
and swaps the global SessionLocal/engine so repositories and routes use it.
"""
import os
import sys
from pathlib import Path

import pytest

# ---- MUST run before importing app modules ----
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890")
os.environ.setdefault("ML_USE_CACHED_MODEL", "false")
os.environ.setdefault("WEATHER_CACHE_TTL_SECONDS", "0")

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import models  # noqa: E402, F401  (register models)
from app.database import session as db_session  # noqa: E402
from app.database.session import Base  # noqa: E402

TEST_ENGINE = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TEST_SESSION = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    db_session.engine = TEST_ENGINE
    db_session.SessionLocal = TEST_SESSION
    Base.metadata.create_all(TEST_ENGINE)
    yield
    Base.metadata.drop_all(TEST_ENGINE)


@pytest.fixture()
def db():
    session = TEST_SESSION()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(_setup_db):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def seed_data(db):
    """Insert a minimal set of categories + destinations (idempotent)."""
    from app.models import Category, Destination

    cat = db.scalars(select(Category).where(Category.slug == "pantai")).first()
    if not cat:
        cat = Category(name="Pantai", slug="pantai", description="Pantai", icon="beach")
        db.add(cat)
        db.commit()
        db.refresh(cat)

    dest = db.scalars(select(Destination).where(Destination.slug == "pantai-indah-tersembunyi")).first()
    if not dest:
        dest = Destination(
            name="Pantai Indah Tersembunyi",
            slug="pantai-indah-tersembunyi",
            category_id=cat.id,
            address="Jl. Pantai No.1",
            province="Jawa Barat",
            regency="Pangandaran",
            district="Kecamatan Pangandaran",
            latitude=-7.7015,
            longitude=108.6525,
            price_min=10000,
            price_max=20000,
            is_free=False,
            opening_time="07:00",
            closing_time="18:00",
            is_open_24h=False,
            days_open=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            facilities=["parkir", "spot_foto"],
            rating=4.6,
            review_count=120,
            popularity=50,
            visitor_count=50000,
            safety=4.2,
            cleanliness=4.0,
            beauty=4.8,
            road_access=3.5,
            crowd_level=3.0,
            hidden_gem_score=78.5,
            phone="081234567890",
        )
        db.add(dest)
        db.commit()
        db.refresh(dest)
    return {"category": cat, "destination": dest}
