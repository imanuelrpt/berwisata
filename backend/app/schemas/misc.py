from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SearchHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: Optional[str]
    filters: Optional[dict]
    result_count: int
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime


class FavoriteCreate(BaseModel):
    destination_id: int


class FavoriteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    destination_id: int
    created_at: datetime
    destination: Optional[dict] = None


class WeatherOut(BaseModel):
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_c: float
    condition: str
    weather_code: int
    wind_speed_kph: float
    wind_direction: float
    humidity: int
    precipitation_mm: float
    is_day: bool
    updated_at: str


class RatingCreate(BaseModel):
    score: float = None
    comment: Optional[str] = None
