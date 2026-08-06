from typing import Optional

from sqlalchemy.orm import Session

from app.models import User
from app.schemas.recommendation import RecommendationRequest
from app.services.recommendation_service import recommend


def get_recommendations(db: Session, payload: RecommendationRequest, user: Optional[User]) -> dict:
    items = recommend(db, payload, user.id if user else None)
    return {
        "items": items,
        "model_available": __import__("app.services.ml_service", fromlist=["model_available"]).model_available(),
        "count": len(items),
    }
