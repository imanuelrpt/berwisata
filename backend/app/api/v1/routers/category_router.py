from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_admin
from app.controllers import category_controller
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=ApiResponse)
def list_categories(db: Session = Depends(get_db_session)):
    return ApiResponse(data=category_controller.list_categories(db))


@router.get("/{category_id}", response_model=ApiResponse)
def get_category(category_id: int, db: Session = Depends(get_db_session)):
    return ApiResponse(data=category_controller.get_category(db, category_id))


@router.post("", response_model=ApiResponse, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db_session), admin=Depends(get_current_admin)):
    return ApiResponse(message="Kategori dibuat", data=category_controller.create_category(db, payload))


@router.patch("/{category_id}", response_model=ApiResponse)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db_session), admin=Depends(get_current_admin)):
    return ApiResponse(message="Kategori diperbarui", data=category_controller.update_category(db, category_id, payload))


@router.delete("/{category_id}", response_model=ApiResponse)
def delete_category(category_id: int, db: Session = Depends(get_db_session), admin=Depends(get_current_admin)):
    return ApiResponse(message="Kategori dihapus", data=category_controller.delete_category(db, category_id))
