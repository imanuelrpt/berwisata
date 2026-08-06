from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.api.deps import get_client_meta
from app.controllers.serializers import serialize_user
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.services import auth_service


def register(db: Session, request: Request, data: RegisterRequest) -> dict:
    meta = get_client_meta(request)
    result = auth_service.register(db, data.email, data.username, data.full_name, data.password, meta["user_agent"], meta["ip"])
    return {"user": serialize_user(result["user"]), "tokens": result["tokens"]}


def login(db: Session, request: Request, data: LoginRequest) -> dict:
    meta = get_client_meta(request)
    result = auth_service.login(db, data.identifier, data.password, meta["user_agent"], meta["ip"])
    return {"user": serialize_user(result["user"]), "tokens": result["tokens"]}


def refresh(db: Session, request: Request, data: RefreshRequest) -> dict:
    meta = get_client_meta(request)
    return auth_service.refresh_token(db, data.refresh_token, meta["user_agent"], meta["ip"])


def logout(db: Session, data: RefreshRequest) -> dict:
    auth_service.logout(db, data.refresh_token)
    return {"message": "Berhasil keluar"}


def me(db: Session, user) -> dict:
    return {"user": serialize_user(user)}
