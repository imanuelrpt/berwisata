from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "BerWisata"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_ORIGIN: str = "http://localhost:5173,http://localhost:8080"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://berwisata:berwisata@localhost:5432/berwisata"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # Storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: str = ".jpg,.jpeg,.png,.webp,.gif"

    # External APIs
    ORS_API_KEY: str = ""
    ORS_BASE_URL: str = "https://api.openrouteservice.org/v2"
    WEATHER_BASE_URL: str = "https://api.open-meteo.com/v1"
    WEATHER_CACHE_TTL_SECONDS: int = 600

    # Machine Learning
    ML_MODEL_PATH: str = "app/ml/models/hidden_gem_model.joblib"
    ML_SCALER_PATH: str = "app/ml/models/scaler.joblib"
    ML_ENCODER_PATH: str = "app/ml/models/label_encoders.joblib"
    ML_FEATURES_PATH: str = "app/ml/models/feature_columns.joblib"
    ML_TRAIN_SPLIT: float = 0.8
    ML_USE_CACHED_MODEL: bool = True
    ML_FALLBACK_WEIGHTS: str = "rating:0.25,review_ratio:0.20,visitor_ratio:0.20,beauty:0.20,access:0.15"

    # WebSocket
    WS_MAX_CLIENTS: int = 5000

    # Rate limiting
    RATE_LIMIT_GLOBAL: str = "2000/minute"
    RATE_LIMIT_AUTH: str = "30/minute"

    # Redis
    REDIS_URL: str = ""

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.FRONTEND_ORIGIN.split(",") if o.strip()]

    @property
    def allowed_extensions(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",")]

    @property
    def upload_path(self) -> str:
        return self.UPLOAD_DIR

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        if v in {"change-me-in-production", "change-me-to-a-long-random-string-in-production"}:
            return v
        if len(v) < 16 and v != "change-me-in-production":
            raise ValueError("SECRET_KEY must be at least 16 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
