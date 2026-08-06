from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session, get_optional_user
from app.controllers import rating_controller
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.misc import RatingCreate

router = APIRouter(prefix="/destinations/{destination_id}/ratings", tags=["Ratings"])


@router.get("", response_model=ApiResponse)
def list_ratings(
    destination_id: int,
    page: int = 1,
    per_page: int = 10,
    db: Session = Depends(get_db_session),
    user: User | None = Depends(get_optional_user),
):
    return ApiResponse(data=rating_controller.list_ratings(db, destination_id, page, per_page))


@router.post("", response_model=ApiResponse, status_code=201)
def add_rating(
    destination_id: int,
    payload: RatingCreate,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    return ApiResponse(message="Rating ditambahkan", data=rating_controller.add_rating(db, user, destination_id, payload))
