from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_optional_user
from app.controllers import recommendation_controller
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.recommendation import RecommendationRequest

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("", response_model=ApiResponse)
def get_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db_session), user: User | None = Depends(get_optional_user)):
    return ApiResponse(data=recommendation_controller.get_recommendations(db, payload, user))
