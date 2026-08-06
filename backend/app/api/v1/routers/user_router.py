from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.controllers import user_controller
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.user import PasswordChange, UserUpdate

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/me", response_model=ApiResponse)
def profile(db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(data=user_controller.get_profile(db, user))


@router.patch("/me", response_model=ApiResponse)
def update_profile(data: UserUpdate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return ApiResponse(data=user_controller.update_profile(db, user, data))


@router.post("/me/avatar", response_model=ApiResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    result = user_controller.upload_avatar(db, user, file)
    return ApiResponse(message="Foto profil diperbarui", data=result)


@router.post("/me/password", response_model=ApiResponse)
def change_password(data: PasswordChange, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    result = user_controller.change_password(db, user, data)
    return ApiResponse(message=result["message"])
