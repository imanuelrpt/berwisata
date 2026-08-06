"""Authentication service: register, login, refresh, logout, token lifecycle."""
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.tracking_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("app.auth")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _as_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _issue_tokens(db: Session, user: User, user_agent: Optional[str], ip: Optional[str]) -> dict:
    access_token = create_access_token(user.email, user.role, user.id)
    refresh_token = create_refresh_token(user.email, user.id)
    repo = RefreshTokenRepository(db)
    repo.create_raw(
        user_id=user.id,
        token_hash=_hash_token(refresh_token),
        user_agent=user_agent[:500] if user_agent else None,
        ip_address=ip,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def register(
    db: Session,
    email: str,
    username: str,
    full_name: str,
    password: str,
    user_agent: Optional[str] = None,
    ip: Optional[str] = None,
) -> dict:
    users = UserRepository(db)
    email = email.lower().strip()
    username = username.strip()

    if users.get_by_email(email):
        raise ConflictError("Email sudah terdaftar", "EMAIL_EXISTS")
    if users.get_by_username(username):
        raise ConflictError("Username sudah digunakan", "USERNAME_EXISTS")

    user = User(
        email=email,
        username=username,
        full_name=full_name.strip(),
        password_hash=hash_password(password),
        role="user",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user registered: %s (%s)", email, username)

    tokens = _issue_tokens(db, user, user_agent, ip)
    return {"user": user, "tokens": tokens}


def login(
    db: Session,
    identifier: str,
    password: str,
    user_agent: Optional[str] = None,
    ip: Optional[str] = None,
) -> dict:
    users = UserRepository(db)
    user = users.get_by_identifier(identifier)
    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Email/username atau password salah", "INVALID_CREDENTIALS")
    if not user.is_active:
        raise ForbiddenError("Akun Anda telah dinonaktifkan", "ACCOUNT_DISABLED")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    tokens = _issue_tokens(db, user, user_agent, ip)
    logger.info("User logged in: %s", user.email)
    return {"user": user, "tokens": tokens}


def refresh_token(db: Session, token: str, user_agent: Optional[str], ip: Optional[str]) -> dict:
    try:
        payload = decode_token(token, expected_type="refresh")
    except ValueError as exc:
        raise UnauthorizedError("Refresh token tidak valid atau kedaluwarsa", "INVALID_REFRESH_TOKEN") from exc

    repo = RefreshTokenRepository(db)
    stored = repo.get_by_hash(_hash_token(token))
    if not stored or stored.revoked_at is not None:
        raise UnauthorizedError("Refresh token sudah tidak aktif", "REFRESH_TOKEN_REVOKED")
    if _as_aware(stored.expires_at) < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token kedaluwarsa", "REFRESH_TOKEN_EXPIRED")

    user = db.get(User, payload.get("uid"))
    if not user or not user.is_active:
        raise UnauthorizedError("User tidak ditemukan", "USER_NOT_FOUND")

    stored.last_used_at = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(user.email, user.role, user.id)
    new_refresh = create_refresh_token(user.email, user.id)
    repo.create_raw(
        user_id=user.id,
        token_hash=_hash_token(new_refresh),
        user_agent=user_agent[:500] if user_agent else None,
        ip_address=ip,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def logout(db: Session, token: str) -> None:
    try:
        payload = decode_token(token, expected_type="refresh")
    except ValueError as exc:
        raise UnauthorizedError("Refresh token tidak valid", "INVALID_REFRESH_TOKEN") from exc
    repo = RefreshTokenRepository(db)
    stored = repo.get_by_hash(_hash_token(token))
    if stored and stored.revoked_at is None:
        repo.revoke(stored)
        db.commit()


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise BadRequestError("Password saat ini salah", "INVALID_CURRENT_PASSWORD")
    user.password_hash = hash_password(new_password)
    repo = RefreshTokenRepository(db)
    repo.revoke_all_for_user(user.id)
    db.commit()
