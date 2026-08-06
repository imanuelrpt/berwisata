from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DashboardStats(BaseModel):
    total_destinations: int
    total_categories: int
    total_users: int
    total_favorites: int
    total_reviews: int
    total_searches: int
    avg_rating: float
    avg_hidden_gem_score: float
    province_distribution: list[dict]
    category_distribution: list[dict]
    top_destinations: list[dict]
    trending_destinations: list[dict]


class TrainingResult(BaseModel):
    status: str
    model_path: str
    samples: int
    features: int
    mae: float
    r2: float
    rmse: float
    accuracy_buckets: dict
    trained_at: str
    retrained_from_scratch: bool = True
