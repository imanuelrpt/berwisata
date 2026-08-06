from typing import Optional

from pydantic import BaseModel, Field


class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: float = Field(0, ge=0)
    speed: float = Field(0, ge=0)
    heading: float = Field(0, ge=0, le=360)


class LocationOut(BaseModel):
    latitude: float
    longitude: float
    accuracy: float
    tracked_at: str


class RouteRequest(BaseModel):
    destination_id: int
    profile: str = Field("driving-car", pattern=r"^(driving-car|driving-hgv|cycling-regular|foot-walking)$")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    model: str = Field("car", pattern=r"^(car|motorcycle|walking|cycling)$")


class RouteResponse(BaseModel):
    distance_km: float
    duration_minutes: float
    polyline: str
    geometry: list[tuple[float, float]]
    profile: str
    source: str  # ors | haversine
    warnings: list[str] = []
