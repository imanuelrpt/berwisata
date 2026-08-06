from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.controllers import auth_controller
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.schemas.common import ApiResponse
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse, status_code=201)
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db_session)):
    result = auth_controller.register(db, request, data)
    return ApiResponse(message="Registrasi berhasil", data=result)


@router.post("/login", response_model=ApiResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db_session)):
    result = auth_controller.login(db, request, data)
    return ApiResponse(message="Login berhasil", data=result)


@router.post("/refresh", response_model=ApiResponse)
def refresh(data: RefreshRequest, request: Request, db: Session = Depends(get_db_session)):
    result = auth_controller.refresh(db, request, data)
    return ApiResponse(message="Token diperbarui", data=result)


@router.post("/logout", response_model=ApiResponse)
def logout(data: RefreshRequest, db: Session = Depends(get_db_session)):
    result = auth_controller.logout(db, data)
    return ApiResponse(message="Berhasil keluar", data=result)


@router.get("/me", response_model=ApiResponse)
def me(db: Session = Depends(get_db_session), user=Depends(get_current_user)):
    return ApiResponse(data=auth_controller.me(db, user))
