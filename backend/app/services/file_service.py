"""Local image upload service with validation + resizing + safe filenames."""
import logging
import secrets
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestError

logger = logging.getLogger("app.files")

_ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_THUMB_SIZE = (1280, 1280)
_AVATAR_SIZE = (512, 512)


def _extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def _validate(ext: str, content_type: str) -> None:
    if ext not in _ALLOWED:
        raise BadRequestError(f"Ekstensi file {ext or '(kosong)'} tidak diizinkan", "INVALID_EXTENSION")
    if not (content_type or "").startswith("image/"):
        raise BadRequestError("File harus berupa gambar", "INVALID_CONTENT_TYPE")


def _read_limited(file: UploadFile, max_bytes: int) -> bytes:
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise BadRequestError(
            f"Ukuran file melebihi batas {settings.MAX_UPLOAD_SIZE_MB}MB", "FILE_TOO_LARGE"
        )
    return data


def save_image(file: UploadFile, folder: str, size: tuple[int, int] = _THUMB_SIZE) -> str:
    """Save image under uploads/<folder>/<token>.<ext> and return relative URL path."""
    ext = _extension(file.filename or "")
    _validate(ext, file.content_type or "")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    data = _read_limited(file, max_bytes)

    try:
        img = PILImage.open(__import__("io").BytesIO(data))
        img = img.convert("RGB") if ext not in (".gif",) else img
        if ext in (".jpg", ".jpeg", ".png", ".webp"):
            img.thumbnail(size, PILImage.LANCZOS)
        token = secrets.token_hex(12)
        out_ext = ext if ext != ".jpeg" else ".jpg"
        rel_path = f"{folder}/{token}{out_ext}"
        target = Path(settings.upload_path) / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        save_kwargs = {"format": "WEBP" if ext == ".webp" else None}
        if out_ext in (".jpg", ".webp"):
            save_kwargs["quality"] = 88
        img.save(target, **save_kwargs)
        logger.info("Saved image %s (%d bytes)", rel_path, len(data))
        return rel_path
    except Exception as exc:
        if isinstance(exc, BadRequestError):
            raise exc
        logger.warning("Image processing failed: %s", exc)
        raise BadRequestError("File gambar tidak valid atau rusak", "INVALID_IMAGE") from exc


def save_avatar(file: UploadFile) -> str:
    return save_image(file, "avatars", _AVATAR_SIZE)


def delete_file(relative_path: Optional[str]) -> None:
    if not relative_path:
        return
    try:
        target = Path(settings.upload_path) / relative_path
        if target.exists() and target.is_file():
            target.unlink()
            logger.info("Deleted file %s", relative_path)
    except OSError as exc:  # pragma: no cover
        logger.warning("Failed to delete %s: %s", relative_path, exc)


def public_url(relative_path: str) -> str:
    return f"/{relative_path}"
