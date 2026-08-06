from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.controllers.serializers import serialize_user
from app.core.exceptions import BadRequestError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import PasswordChange, UserUpdate
from app.services import auth_service, file_service


def get_profile(db: Session, user: User) -> dict:
    return {"user": serialize_user(user)}


def update_profile(db: Session, user: User, data: UserUpdate) -> dict:
    repo = UserRepository(db)
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return {"user": serialize_user(user)}


def upload_avatar(db: Session, user: User, file: UploadFile) -> dict:
    old = user.avatar_url
    rel = file_service.save_avatar(file)
    user.avatar_url = file_service.public_url(rel)
    db.commit()
    if old and old != user.avatar_url:
        file_service.delete_file(old.lstrip("/"))
    return {"user": serialize_user(user)}


def change_password(db: Session, user: User, data: PasswordChange) -> dict:
    auth_service.change_password(db, user, data.current_password, data.new_password)
    return {"message": "Password berhasil diubah, silakan login kembali"}
