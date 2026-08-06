from typing import Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    categories: Optional[list[str]] = Field(None, max_length=10)
    budget: Optional[float] = Field(None, ge=0)
    radius_km: Optional[float] = Field(None, ge=1, le=2000)
    not_crowded: bool = False
    preferences: Optional[list[str]] = Field(None, max_length=10)
    limit: int = Field(10, ge=1, le=50)


class RecommendationItem(BaseModel):
    destination: dict
    hidden_gem_score: float
    match_reason: str
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None
