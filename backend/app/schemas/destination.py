from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.category import CategoryOut


class DestinationBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    category_id: int = Field(..., gt=0)
    summary: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    address: str = Field(..., min_length=5, max_length=500)
    province: str = Field(..., min_length=3, max_length=100)
    regency: str = Field(..., min_length=3, max_length=120)
    district: Optional[str] = Field(None, max_length=120)
    village: Optional[str] = Field(None, max_length=120)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    price_min: float = Field(0, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    is_free: bool = False
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    is_open_24h: bool = False
    days_open: list[str] = Field(
        default_factory=lambda: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    )
    facilities: list[str] = Field(default_factory=list)
    rating: float = Field(0, ge=0, le=5)
    review_count: int = Field(0, ge=0)
    popularity: int = Field(0, ge=0)
    visitor_count: int = Field(0, ge=0)
    safety: float = Field(4.0, ge=1, le=5)
    cleanliness: float = Field(4.0, ge=1, le=5)
    beauty: float = Field(4.0, ge=1, le=5)
    road_access: float = Field(4.0, ge=1, le=5)
    crowd_level: float = Field(3.0, ge=1, le=5)
    phone: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    is_featured: bool = False
    is_trending: bool = False

    @field_validator("latitude", "longitude")
    @classmethod
    def valid_coordinates(cls, v: float) -> float:
        if v == 0:
            return v
        return v

    @field_validator("opening_time", "closing_time")
    @classmethod
    def validate_time(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re

        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v):
            raise ValueError("Format waktu harus HH:MM")
        return v

    @field_validator("website", "instagram")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("URL harus diawali http:// atau https://")
        return v


class DestinationCreate(DestinationBase):
    images: list[str] = Field(default_factory=list)


class DestinationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    category_id: Optional[int] = Field(None, gt=0)
    summary: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    province: Optional[str] = Field(None, min_length=3, max_length=100)
    regency: Optional[str] = Field(None, min_length=3, max_length=120)
    district: Optional[str] = Field(None, max_length=120)
    village: Optional[str] = Field(None, max_length=120)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    is_free: Optional[bool] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    is_open_24h: Optional[bool] = None
    days_open: Optional[list[str]] = None
    facilities: Optional[list[str]] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
    popularity: Optional[int] = Field(None, ge=0)
    visitor_count: Optional[int] = Field(None, ge=0)
    safety: Optional[float] = Field(None, ge=1, le=5)
    cleanliness: Optional[float] = Field(None, ge=1, le=5)
    beauty: Optional[float] = Field(None, ge=1, le=5)
    road_access: Optional[float] = Field(None, ge=1, le=5)
    crowd_level: Optional[float] = Field(None, ge=1, le=5)
    phone: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    is_featured: Optional[bool] = None
    is_trending: Optional[bool] = None


class ImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    caption: Optional[str]
    is_primary: bool
    sort_order: int


class DestinationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    category_id: int
    category: Optional[CategoryOut] = None
    summary: Optional[str]
    description: Optional[str]
    address: str
    province: str
    regency: str
    district: Optional[str]
    village: Optional[str]
    latitude: float
    longitude: float
    price_min: float
    price_max: Optional[float]
    is_free: bool
    currency: str
    opening_time: Optional[str]
    closing_time: Optional[str]
    is_open_24h: bool
    days_open: list[str]
    facilities: list[str]
    rating: float
    review_count: int
    popularity: int
    visitor_count: int
    hidden_gem_score: float
    phone: Optional[str]
    website: Optional[str]
    instagram: Optional[str]
    is_featured: bool
    is_trending: bool
    view_count: int
    images: list[ImageOut] = Field(default_factory=list)
    created_at: datetime
    # computed (filled by service when context available)
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None
    weather: Optional[dict] = None
    is_favorited: bool = False

    @property
    def primary_image(self) -> Optional[str]:
        for img in self.images:
            if img.is_primary:
                return img.url
        return self.images[0].url if self.images else None

    @property
    def price_label(self) -> str:
        if self.is_free or (self.price_min == 0 and not self.price_max):
            return "Gratis"
        if self.price_max and self.price_max > self.price_min:
            return f"Rp{int(self.price_min):,} - Rp{int(self.price_max):,}"
        return f"Rp{int(self.price_min):,}"


class DestinationDetailOut(DestinationOut):
    weather: Optional[dict] = None
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None
