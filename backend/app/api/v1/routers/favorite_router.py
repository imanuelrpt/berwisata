from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.controllers import favorite_controller
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.misc import FavoriteCreate

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=ApiResponse)
def list_favorites(page: int = 1, per_page: int = 12, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(data=favorite_controller.list_favorites(db, user, page, per_page))


@router.post("", response_model=ApiResponse, status_code=201)
def add_favorite(payload: FavoriteCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(message="Ditambahkan ke favorit", data=favorite_controller.add_favorite(db, user, payload))


@router.delete("/{destination_id}", response_model=ApiResponse)
def remove_favorite(destination_id: int, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(message="Dihapus dari favorit", data=favorite_controller.remove_favorite(db, user, destination_id))
