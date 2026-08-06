from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.database.session import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db_session() -> Session:
    yield from get_db()


def get_client_meta(request: Request) -> dict:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return {"ip": ip, "user_agent": ua}


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db_session),
) -> User:
    if not credentials:
        raise UnauthorizedError("Autentikasi diperlukan", "AUTH_REQUIRED")
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except ValueError as exc:
        raise UnauthorizedError(str(exc), "INVALID_TOKEN") from exc

    user = db.get(User, payload.get("uid"))
    if not user:
        raise UnauthorizedError("User tidak ditemukan", "USER_NOT_FOUND")
    if not user.is_active:
        raise ForbiddenError("Akun Anda telah dinonaktifkan", "ACCOUNT_DISABLED")
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise ForbiddenError("Akses khusus admin", "ADMIN_REQUIRED")
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db_session),
) -> Optional[User]:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except ValueError:
        return None
    user = db.get(User, payload.get("uid"))
    return user if user and user.is_active else None
