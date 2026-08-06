from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=200)
    province: Optional[str] = Field(None, max_length=100)
    regency: Optional[str] = Field(None, max_length=120)
    category_id: Optional[int] = None
    category_slug: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    is_free: Optional[bool] = None
    radius_km: Optional[float] = Field(None, gt=0, le=2000)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    budget: Optional[float] = Field(None, ge=0)
    is_open_now: Optional[bool] = None
    facilities: Optional[list[str]] = Field(None, max_length=20)
    tags: Optional[list[str]] = Field(None, max_length=20)  # gunung/pantai/air terjun/danau/camping/tracking/sunrise/sunset
    audience: Optional[list[str]] = Field(None, max_length=10)  # anak/keluarga/pasangan/solo
    min_hidden_gem_score: Optional[float] = Field(None, ge=0, le=100)
    sort_by: Optional[str] = Field(None, pattern=r"^(relevance|distance|rating|price_asc|price_desc|hidden_gem|popular|trending)$")
    order: Optional[str] = Field("desc", pattern=r"^(asc|desc)$")
    page: int = Field(1, ge=1)
    per_page: int = Field(12, ge=1, le=50)


class SavedSearch(BaseModel):
    query: str
    filters: dict
    result_count: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
