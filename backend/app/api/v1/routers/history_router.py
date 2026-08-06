from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.controllers import tracking_controller
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.location import LocationUpdate
from app.schemas.misc import SearchHistoryOut
from app.schemas.search import SavedSearch

router = APIRouter(tags=["Tracking & History"])


@router.post("/search-history", response_model=ApiResponse)
def save_search(payload: SavedSearch, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(data=tracking_controller.save_search(db, user, payload))


@router.get("/search-history", response_model=ApiResponse)
def list_history(limit: int = 20, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(data=tracking_controller.list_history(db, user, limit))


@router.delete("/search-history", response_model=ApiResponse)
def delete_history(history_id: int | None = None, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(data=tracking_controller.delete_history(db, user, history_id))


@router.post("/location", response_model=ApiResponse)
def update_location(payload: LocationUpdate, request: Request, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(data=tracking_controller.update_location(db, user, payload, request))


@router.get("/location", response_model=ApiResponse)
def get_location(db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(data=tracking_controller.get_latest_location(db, user))
