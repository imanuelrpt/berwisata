from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: int = 0
    parent_id: Optional[int] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = Field(None, min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None
    parent_id: Optional[int] = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str]
    icon: Optional[str]
    image_url: Optional[str]
    sort_order: int
    parent_id: Optional[int]
    destination_count: int = 0
    created_at: datetime
