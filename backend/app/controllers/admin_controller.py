import csv
import io
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import Category, Destination, DestinationImage, Favorite, Rating, SearchHistory, User
from app.repositories.destination_repository import DestinationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.category import CategoryCreate
from app.schemas.destination import DestinationCreate, DestinationUpdate
from app.services import destination_service
from app.services.ml_service import reload_model, training_metadata

logger = logging.getLogger("app.admin")

CATEGORY_NAMES = [
    "gunung", "bukit", "pantai", "pulau", "air-terjun", "curug", "danau",
    "camping", "tracking", "sunrise", "sunset", "gua", "taman", "desa-wisata", "pemandian",
    "budaya", "religi",
]


def dashboard_stats(db: Session) -> dict:
    total_dest = int(db.scalar(select(func.count(Destination.id))) or 0)
    total_cats = int(db.scalar(select(func.count(Category.id))) or 0)
    total_users = int(db.scalar(select(func.count(User.id))) or 0)
    total_fav = int(db.scalar(select(func.count(Favorite.id))) or 0)
    total_rev = int(db.scalar(select(func.count(Rating.id))) or 0)
    total_search = int(db.scalar(select(func.count(SearchHistory.id))) or 0)
    avg_rating = float(db.scalar(select(func.avg(Destination.rating))) or 0)
    avg_score = float(db.scalar(select(func.avg(Destination.hidden_gem_score))) or 0)

    province_rows = db.execute(
        select(Destination.province, func.count(Destination.id)).group_by(Destination.province).order_by(func.count(Destination.id).desc()).limit(10)
    ).all()
    category_rows = db.execute(
        select(Category.name, func.count(Destination.id))
        .join(Destination, Destination.category_id == Category.id)
        .group_by(Category.name)
        .order_by(func.count(Destination.id).desc())
        .limit(10)
    ).all()

    top = db.execute(
        select(Destination).order_by(Destination.hidden_gem_score.desc()).limit(5)
    ).scalars().all()
    trending = db.execute(
        select(Destination).where(Destination.is_trending.is_(True)).order_by(Destination.popularity.desc()).limit(5)
    ).scalars().all()

    return {
        "total_destinations": total_dest,
        "total_categories": total_cats,
        "total_users": total_users,
        "total_favorites": total_fav,
        "total_reviews": total_rev,
        "total_searches": total_search,
        "avg_rating": round(avg_rating, 2),
        "avg_hidden_gem_score": round(avg_score, 2),
        "province_distribution": [{"name": p, "count": c} for p, c in province_rows],
        "category_distribution": [{"name": n, "count": c} for n, c in category_rows],
        "top_destinations": [destination_service.serialize_destination(d) for d in top],
        "trending_destinations": [destination_service.serialize_destination(d) for d in trending],
        "model": training_metadata(),
    }


def list_users(db: Session, page: int, per_page: int, role: Optional[str], query: Optional[str]) -> dict:
    repo = UserRepository(db)
    rows, total = repo.list_paginated(page, per_page, role, query)
    return {
        "data": [
            {
                "id": u.id, "email": u.email, "username": u.username, "full_name": u.full_name,
                "avatar_url": u.avatar_url, "role": u.role, "is_active": u.is_active,
                "is_verified": u.is_verified, "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in rows
        ],
        "meta": _meta(page, per_page, total),
    }


def update_user_status(db: Session, user_id: int, is_active: bool) -> dict:
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise NotFoundError("User tidak ditemukan", "USER_NOT_FOUND")
    user.is_active = is_active
    db.commit()
    return {"message": "Status user diperbarui", "is_active": user.is_active}


def delete_user(db: Session, user_id: int) -> dict:
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise NotFoundError("User tidak ditemukan", "USER_NOT_FOUND")
    if user.role == "admin":
        raise BadRequestError("Admin tidak dapat dihapus", "CANNOT_DELETE_ADMIN")
    repo.delete(user)
    return {"message": "User dihapus"}


def retrain_model(db: Session, data_path: Optional[str] = None) -> dict:
    from app.ml.train import load_dataset, train_model
    from app.core.config import settings
    from pathlib import Path

    path = Path(data_path or "app/ml/data/destinations.csv")
    if not path.exists():
        raise BadRequestError("Dataset tidak ditemukan", "DATASET_NOT_FOUND")
    df = load_dataset(path)
    model_dir = Path(settings.ML_MODEL_PATH).parent
    artifacts = train_model(df, model_dir)
    ok = reload_model()

    # Recompute scores for all destinations using the fresh model
    rows = list(db.scalars(select(Destination).limit(2000)).all())
    destination_service.apply_hidden_gem_scores(rows)
    db.commit()

    return {
        "status": "success" if ok else "partial",
        "model_path": artifacts["model_path"],
        "samples": artifacts["samples"],
        "features": artifacts["features"],
        "mae": artifacts["mae"],
        "r2": artifacts["r2"],
        "rmse": artifacts["rmse"],
        "accuracy_buckets": artifacts["accuracy_buckets"],
        "trained_at": artifacts["trained_at"],
    }


def export_csv(db: Session) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    header = [
        "name", "slug", "category", "province", "regency", "district", "village", "address",
        "latitude", "longitude", "price_min", "price_max", "is_free", "opening_time", "closing_time",
        "is_open_24h", "days_open", "facilities", "rating", "review_count", "popularity",
        "visitor_count", "safety", "cleanliness", "beauty", "road_access", "crowd_level",
        "hidden_gem_score", "phone", "is_trending", "is_featured",
    ]
    writer.writerow(header)
    rows = list(db.scalars(select(Destination)).yield_per(500))
    for d in rows:
        writer.writerow([
            d.name, d.slug, d.category.slug if d.category else "", d.province, d.regency,
            d.district or "", d.village or "", d.address, d.latitude, d.longitude,
            d.price_min, d.price_max or "", int(d.is_free), d.opening_time or "", d.closing_time or "",
            int(d.is_open_24h), "|".join(d.days_open or []), "|".join(d.facilities or []),
            d.rating, d.review_count, d.popularity, d.visitor_count,
            d.safety, d.cleanliness, d.beauty, d.road_access, d.crowd_level,
            d.hidden_gem_score, d.phone or "", int(d.is_trending), int(d.is_featured),
        ])
    return buffer.getvalue()


def import_csv(db: Session, content: str) -> dict:
    repo = DestinationRepository(db)
    reader = csv.DictReader(io.StringIO(content))
    required = {"name", "category", "province", "regency", "latitude", "longitude"}
    imported = skipped = 0
    categories = {c.slug: c.id for c in db.scalars(select(Category)).all()}
    for slug in CATEGORY_NAMES:
        if slug not in categories:
            cat = Category(name=slug.replace("-", " ").title(), slug=slug)
            db.add(cat)
            db.commit()
            db.refresh(cat)
            categories[slug] = cat.id

    for raw in reader:
        try:
            if not raw.get("name") or not raw.get("latitude") or not raw.get("longitude"):
                skipped += 1
                continue
            cat_slug = raw.get("category", "").strip().replace(" ", "-").lower() or "taman"
            cat_slug = cat_slug if cat_slug in categories else "taman"
            if repo.get_by_slug(_slug(raw["name"])):
                skipped += 1
                continue
            days = [x for x in raw.get("days_open", "mon|tue|wed|thu|fri|sat|sun").split("|") if x]
            facilities = [x for x in raw.get("facilities", "").split("|") if x]
            images = [x.strip() for x in raw.get("images", "").split("|") if x.strip()]

            dest = Destination(
                name=raw["name"],
                slug=_slug(raw["name"]),
                category_id=categories[cat_slug],
                summary=raw.get("summary") or None,
                description=raw.get("description") or None,
                address=raw.get("address") or raw["name"],
                province=raw.get("province", ""),
                regency=raw.get("regency", ""),
                district=raw.get("district") or None,
                village=raw.get("village") or None,
                latitude=float(raw["latitude"]),
                longitude=float(raw["longitude"]),
                price_min=float(raw.get("price_min", 0) or 0),
                price_max=float(raw["price_max"]) if raw.get("price_max") else None,
                is_free=_to_bool(raw.get("is_free")),
                opening_time=raw.get("opening_time") or "08:00",
                closing_time=raw.get("closing_time") or "17:00",
                is_open_24h=_to_bool(raw.get("is_open_24h")),
                days_open=days,
                facilities=facilities,
                rating=float(raw.get("rating", 4.0)),
                review_count=int(raw.get("review_count", 0)),
                popularity=int(raw.get("popularity", 10)),
                visitor_count=int(raw.get("visitor_count", 1000)),
                safety=float(raw.get("safety", 4.0)),
                cleanliness=float(raw.get("cleanliness", 4.0)),
                beauty=float(raw.get("beauty", 4.0)),
                road_access=float(raw.get("road_access", 3.5)),
                crowd_level=float(raw.get("crowd_level", 3.0)),
                hidden_gem_score=float(raw.get("hidden_gem_score", 50.0)),
                phone=raw.get("phone") or None,
                is_trending=_to_bool(raw.get("is_trending")),
                is_featured=_to_bool(raw.get("is_featured")),
            )
            db.add(dest)
            for idx, url in enumerate(images):
                db.add(DestinationImage(
                    destination=dest,
                    url=url,
                    is_primary=idx == 0,
                    sort_order=idx,
                    caption=None,
                ))
            imported += 1
            if imported % 500 == 0:
                db.flush()
        except (ValueError, KeyError) as exc:
            logger.warning("Skipped CSV row: %s", exc)
            skipped += 1
    db.commit()
    logger.info("CSV import: %d imported, %d skipped", imported, skipped)
    return {"imported": imported, "skipped": skipped}


def _to_bool(value) -> bool:
    if value is None or str(value).strip() == "":
        return False
    v = str(value).strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


def _slug(name: str) -> str:
    import re
    import unicodedata

    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower() or "destinasi"


def _meta(page: int, per_page: int, total: int) -> dict:
    pages = max(1, (total + per_page - 1) // per_page)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
