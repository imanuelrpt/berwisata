"""Smart recommendation service powered by the ML model."""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.destination_repository import DestinationRepository
from app.schemas.recommendation import RecommendationRequest
from app.services import ml_service
from app.services.destination_service import (
    _destination_features,
    _build_query,
    serialize_destination,
)
from app.utils.geo import haversine_km

logger = logging.getLogger("app.recommendation")


def recommend(db: Session, req: RecommendationRequest, user_id: Optional[int] = None) -> list[dict]:
    filters = {}
    if req.categories:
        filters["tags"] = req.categories
    if req.budget is not None:
        filters["budget"] = req.budget
    if req.radius_km is not None:
        filters["radius_km"] = req.radius_km
        filters["latitude"] = req.latitude
        filters["longitude"] = req.longitude
    if req.not_crowded:
        filters["tags"] = filters.get("tags") or []
        filters["tags"] = [t for t in filters["tags"] if t != "tidak-ramai"]

    stmt = _build_query(db, **filters)
    candidates = list(db.scalars(stmt.limit(300)).all())

    if req.not_crowded:
        candidates = [c for c in candidates if c.crowd_level <= 3.5]

    # Build feature rows for the ML model
    feature_rows = [_destination_features(c) for c in candidates]
    scores = ml_service.predict_scores(feature_rows)

    scored = []
    for c, score in zip(candidates, scores):
        rec = {
            "destination": serialize_destination(c),
            "hidden_gem_score": round(float(score), 2),
            "match_reason": _reason(c, score, req),
        }
        if req.latitude is not None and req.longitude is not None:
            rec["distance_km"] = round(
                haversine_km(req.latitude, req.longitude, c.latitude, c.longitude), 2
            )
            rec["duration_minutes"] = round(rec["distance_km"] / 55.0 * 60.0, 1)
        scored.append(rec)

    # Sort primarily by ML score; apply preference boosts
    boost = {}
    if req.not_crowded:
        boost["not_crowded"] = True
    for pref in (req.preferences or []):
        boost.setdefault(pref.lower(), 1.0)

    def sort_key(item):
        base = item["hidden_gem_score"]
        if boost.get("not_crowded"):
            base += 3
        cat_slug = item["destination"]["category"]["slug"] if item["destination"].get("category") else ""
        if cat_slug and cat_slug in boost:
            base += 5
        if req.latitude is not None and item.get("distance_km") is not None:
            base += max(0.0, 4.0 - item["distance_km"] / 50.0)
        return base

    scored.sort(key=sort_key, reverse=True)
    return scored[: req.limit]


def _reason(c, score: float, req: RecommendationRequest) -> str:
    parts = []
    if score >= 75:
        parts.append("Hidden gem dengan skor sangat tinggi")
    elif score >= 55:
        parts.append("Hidden gem dengan skor baik")
    else:
        parts.append("Destinasi menarik untuk dikunjungi")
    if req.not_crowded and c.crowd_level <= 3.0:
        parts.append("cocok untuk yang menghindari keramaian")
    if c.is_free:
        parts.append("gratis")
    if c.rating >= 4.5:
        parts.append(f"rating {c.rating:.1f}")
    return ", ".join(parts)
