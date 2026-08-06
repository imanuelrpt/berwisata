"""Destination service: search engine, filters, scoring, distance/weather enrichment."""
import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import Category, Destination, User
from app.repositories.destination_repository import DestinationRepository
from app.schemas.destination import DestinationCreate, DestinationUpdate
from app.services import ml_service
from app.services.map_service import distance_matrix
from app.services.weather_service import attach_weather
from app.utils.geo import haversine_km

logger = logging.getLogger("app.destination")

TAG_TO_CATEGORY = {
    "gunung": "gunung",
    "pantai": "pantai",
    "air terjun": "air-terjun",
    "airterjun": "air-terjun",
    "danau": "danau",
    "camping": "camping",
    "tracking": "tracking",
    "trekking": "tracking",
    "sunrise": "sunrise",
    "sunset": "sunset",
    "gua": "gua",
    "bukit": "bukit",
    "pulau": "pulau",
    "taman": "taman",
    "desa wisata": "desa-wisata",
    "pemandian": "pemandian",
}

AUDIENCE_FACILITIES = {
    "anak": "anak",
    "keluarga": "keluarga",
    "pasangan": "pasangan",
    "solo": "solo",
}


def _build_query(
    db: Session,
    *,
    query: Optional[str] = None,
    province: Optional[str] = None,
    regency: Optional[str] = None,
    category_id: Optional[int] = None,
    category_slug: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    is_free: Optional[bool] = None,
    radius_km: Optional[float] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    budget: Optional[float] = None,
    is_open_now: Optional[bool] = None,
    facilities: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    audience: Optional[list[str]] = None,
    min_hidden_gem_score: Optional[float] = None,
):
    stmt = select(Destination)
    conditions = []

    if query:
        like = f"%{query.strip().lower()}%"
        conditions.append(Destination.name.ilike(like))

    if province:
        conditions.append(Destination.province.ilike(f"%{province.strip()}%"))
    if regency:
        conditions.append(Destination.regency.ilike(f"%{regency.strip()}%"))

    if category_id is not None:
        conditions.append(Destination.category_id == category_id)
    if category_slug:
        slug_cond = select(Category.id).where(Category.slug == category_slug).scalar_subquery()
        conditions.append(Destination.category_id.in_(slug_cond))

    if min_price is not None or max_price is not None:
        if min_price is not None:
            conditions.append(Destination.price_min >= min_price)
        if max_price is not None:
            conditions.append(Destination.price_min <= max_price)

    if budget is not None:
        conditions.append(Destination.price_min <= budget)

    if min_rating is not None:
        conditions.append(Destination.rating >= min_rating)

    if is_free is not None:
        conditions.append(Destination.is_free == is_free)

    if min_hidden_gem_score is not None:
        conditions.append(Destination.hidden_gem_score >= min_hidden_gem_score)

    if is_open_now:
        from datetime import datetime

        now = datetime.now()
        conditions.append(Destination.is_open_24h.is_(True))
        hour = now.strftime("%H:%M")
        conditions.append(
            func.concat(Destination.opening_time, "-", Destination.closing_time) != None  # noqa: E711
        )
        conditions.append(Destination.opening_time <= hour)
        conditions.append(Destination.closing_time >= hour)

    if facilities:
        for f in facilities:
            conditions.append(Destination.facilities.contains([f]))

    if tags:
        cat_slugs = [TAG_TO_CATEGORY.get(t.lower().strip(), t.lower().replace(" ", "-")) for t in tags]
        for slug in cat_slugs:
            if slug == "gratis":
                conditions.append(Destination.is_free.is_(True))
            elif slug == "berbayar":
                conditions.append(Destination.is_free.is_(False))
            else:
                sub = select(Category.id).where(Category.slug == slug).scalar_subquery()
                conditions.append(Destination.category_id.in_(sub))

    if audience:
        for a in audience:
            if a.lower() in AUDIENCE_FACILITIES:
                conditions.append(Destination.facilities.contains([AUDIENCE_FACILITIES[a.lower()]]))

    # radius bounding-box pre-filter
    if radius_km is not None and latitude is not None and longitude is not None:
        if radius_km > 0:
            deg_lat = radius_km / 111.0
            deg_lon = radius_km / (111.0 * max(0.01, abs(__import__("math").cos(__import__("math").radians(latitude)))))
            conditions.append(Destination.latitude.between(latitude - deg_lat, latitude + deg_lat))
            conditions.append(Destination.longitude.between(longitude - deg_lon, longitude + deg_lon))

    for cond in conditions:
        stmt = stmt.where(cond)
    return stmt


def search_destinations(
    db: Session,
    *,
    page: int,
    per_page: int,
    sort_by: Optional[str] = None,
    order: str = "desc",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    **filters,
) -> tuple[list[Destination], int]:
    stmt = _build_query(db, **filters)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(db.scalar(count_stmt) or 0)

    sort_map = {
        "rating": Destination.rating,
        "price_asc": Destination.price_min,
        "price_desc": Destination.price_min,
        "hidden_gem": Destination.hidden_gem_score,
        "popular": Destination.popularity,
        "trending": Destination.popularity,
        "relevance": Destination.created_at,
    }

    if sort_by and sort_by != "distance":
        col = sort_map.get(sort_by)
        if col is not None:
            if sort_by == "price_asc":
                stmt = stmt.order_by(col.asc())
            elif sort_by == "price_desc":
                stmt = stmt.order_by(col.desc())
            else:
                stmt = stmt.order_by(col.desc() if order == "desc" else col.asc())
    elif sort_by == "distance" and latitude is not None and longitude is not None:
        pass  # sorted in python
    else:
        stmt = stmt.order_by(Destination.created_at.desc())

    rows = list(db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all())

    if sort_by == "distance" and latitude is not None and longitude is not None:
        rows.sort(
            key=lambda d: haversine_km(latitude, longitude, d.latitude, d.longitude),
            reverse=(order == "desc"),
        )

    return rows, total


def apply_hidden_gem_scores(rows: list[Destination]) -> None:
    """Recompute hidden_gem_score with the ML model for provided destination rows."""
    payload = [_destination_features(d) for d in rows]
    scores = ml_service.predict_scores(payload)
    for d, score in zip(rows, scores):
        d.hidden_gem_score = score


def _destination_features(d: Destination) -> dict:
    return {
        "category": d.category.slug if d.category else "unknown",
        "province": d.province,
        "regency": d.regency,
        "rating": d.rating,
        "review_count": d.review_count,
        "price_min": float(d.price_min),
        "popularity": d.popularity,
        "visitor_count": d.visitor_count,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "safety": d.safety,
        "cleanliness": d.cleanliness,
        "beauty": d.beauty,
        "road_access": d.road_access,
        "crowd_level": d.crowd_level,
        "is_free": d.is_free,
        "is_open_24h": d.is_open_24h,
        "opening_time": d.opening_time or "08:00",
        "closing_time": d.closing_time or "17:00",
        "facilities": d.facilities or [],
    }


def serialize_destination(d: Destination, *, include_weather: bool = False,
                          include_description: bool = False) -> dict:
    data = {
        "id": d.id,
        "name": d.name,
        "slug": d.slug,
        "category_id": d.category_id,
        "category": {
            "id": d.category.id,
            "name": d.category.name,
            "slug": d.category.slug,
            "icon": d.category.icon,
        } if d.category else None,
        "summary": d.summary,
        "address": d.address,
        "province": d.province,
        "regency": d.regency,
        "district": d.district,
        "village": d.village,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "price_min": float(d.price_min),
        "price_max": float(d.price_max) if d.price_max else None,
        "is_free": d.is_free,
        "currency": d.currency,
        "opening_time": d.opening_time,
        "closing_time": d.closing_time,
        "is_open_24h": d.is_open_24h,
        "days_open": d.days_open or [],
        "facilities": d.facilities or [],
        "rating": round(d.rating, 2),
        "review_count": d.review_count,
        "popularity": d.popularity,
        "visitor_count": d.visitor_count,
        "hidden_gem_score": round(d.hidden_gem_score, 2),
        "phone": d.phone,
        "website": d.website,
        "instagram": d.instagram,
        "is_featured": d.is_featured,
        "is_trending": d.is_trending,
        "view_count": d.view_count,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "images": [
            {
                "id": img.id,
                "url": img.url,
                "caption": img.caption,
                "is_primary": img.is_primary,
                "sort_order": img.sort_order,
            }
            for img in (d.images or [])
        ],
    }
    if include_description:
        data["description"] = d.description
    if include_weather:
        data["weather"] = None
    return data


def enrich_with_weather_and_distance(
    data_list: list[dict],
    latitude: Optional[float],
    longitude: Optional[float],
    user: Optional[User] = None,
    favorite_ids: Optional[set[int]] = None,
) -> list[dict]:
    for d in data_list:
        if latitude is not None and longitude is not None:
            d["distance_km"] = round(
                haversine_km(latitude, longitude, d["latitude"], d["longitude"]), 2
            )
            d["duration_minutes"] = None  # computed via route endpoint
        else:
            d["distance_km"] = None
            d["duration_minutes"] = None
        if favorite_ids:
            d["is_favorited"] = d["id"] in favorite_ids
    return data_list


def get_destination_or_404(db: Session, destination_id: int) -> Destination:
    repo = DestinationRepository(db)
    dest = repo.get(destination_id)
    if not dest:
        raise NotFoundError("Destinasi tidak ditemukan", "DESTINATION_NOT_FOUND")
    return dest


def create_destination(db: Session, data: DestinationCreate) -> Destination:
    repo = DestinationRepository(db)
    if repo.get_by_slug(_slugify(data.name)):
        raise BadRequestError("Destinasi dengan nama serupa sudah ada", "DUPLICATE_DESTINATION")
    payload = data.model_dump(exclude={"images"})
    dest = repo.create_raw(**payload)
    if data.images:
        for i, url in enumerate(data.images):
            repo.add_image(dest.id, url, None, i == 0, i)
    db.commit()
    db.refresh(dest)
    apply_hidden_gem_scores([dest])
    db.commit()
    return dest


def update_destination(db: Session, dest: Destination, data: DestinationUpdate) -> Destination:
    repo = DestinationRepository(db)
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(dest, k, v)
    if "name" in updates:
        dest.slug = _slugify(dest.name)
    db.commit()
    db.refresh(dest)
    apply_hidden_gem_scores([dest])
    db.commit()
    return dest


def _slugify(name: str) -> str:
    import re
    import unicodedata

    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "destinasi"


def delete_destination(db: Session, dest: Destination) -> None:
    repo = DestinationRepository(db)
    repo.delete(dest)
