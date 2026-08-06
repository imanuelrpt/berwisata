from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


def list_categories(db: Session) -> dict:
    repo = CategoryRepository(db)
    rows = repo.list_with_counts()
    return {
        "data": [
            {
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "description": cat.description,
                "icon": cat.icon,
                "image_url": cat.image_url,
                "sort_order": cat.sort_order,
                "parent_id": cat.parent_id,
                "destination_count": count,
                "created_at": cat.created_at.isoformat() if cat.created_at else None,
            }
            for cat, count in rows
        ]
    }


def get_category(db: Session, category_id: int) -> dict:
    repo = CategoryRepository(db)
    cat = repo.get(category_id)
    if not cat:
        raise NotFoundError("Kategori tidak ditemukan", "CATEGORY_NOT_FOUND")
    return {"category": cat}


def create_category(db: Session, payload: CategoryCreate) -> dict:
    repo = CategoryRepository(db)
    if repo.get_by_slug(payload.slug):
        raise BadRequestError("Slug kategori sudah ada", "SLUG_EXISTS")
    cat = repo.create(payload)
    return {"category": cat}


def update_category(db: Session, category_id: int, payload: CategoryUpdate) -> dict:
    repo = CategoryRepository(db)
    cat = repo.get(category_id)
    if not cat:
        raise NotFoundError("Kategori tidak ditemukan", "CATEGORY_NOT_FOUND")
    cat = repo.update(cat, payload)
    return {"category": cat}


def delete_category(db: Session, category_id: int) -> dict:
    repo = CategoryRepository(db)
    cat = repo.get(category_id)
    if not cat:
        raise NotFoundError("Kategori tidak ditemukan", "CATEGORY_NOT_FOUND")
    repo.delete(cat)
    return {"message": "Kategori dihapus"}
