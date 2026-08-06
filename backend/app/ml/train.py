"""
Machine Learning training pipeline for BerWisata.

Trains a Random Forest regressor on the destinations dataset to predict the
Hidden Gem Score (0-100) and serializes model artifacts with joblib.

Usage:
    python -m app.ml.train --data app/ml/data/destinations.csv
    python -m app.ml.train --data app/ml/data/destinations.csv --output app/ml/models/
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from app.core.config import settings

TARGET = "hidden_gem_score"
RNG_SEED = 42

CATEGORICAL_COLUMNS = ["category", "province", "regency"]
NUMERIC_COLUMNS = [
    "rating",
    "review_count",
    "price_min",
    "popularity",
    "visitor_count",
    "latitude",
    "longitude",
    "safety",
    "cleanliness",
    "beauty",
    "road_access",
    "crowd_level",
    "is_free",
    "is_open_24h",
    "opening_hour",
    "closing_hour",
    "facility_count",
    "has_parking",
    "has_food",
    "has_guide",
    "has_camping",
    "has_wifi",
    "log_visitor",
]


def _default_feature_df(rows: list[dict]) -> pd.DataFrame:
    """Build a DataFrame with the full feature schema (used when columns missing)."""
    df = pd.DataFrame(rows)
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
    for col in CATEGORICAL_COLUMNS:
        if col not in df.columns:
            df[col] = "unknown"
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw rows into model-ready feature columns."""
    out = df.copy()
    out["is_free"] = out["is_free"].astype(int)
    out["is_open_24h"] = out["is_open_24h"].astype(int)

    out["opening_hour"] = pd.to_numeric(out["opening_time"].fillna("08:00").str.split(":").str[0], errors="coerce").fillna(8)
    out["closing_hour"] = pd.to_numeric(out["closing_time"].fillna("17:00").str.split(":").str[0], errors="coerce").fillna(17)
    if out["opening_hour"].nunique() < 2 and out["opening_hour"].iloc[0] == 0:
        out["opening_hour"] = 0
    if out["closing_hour"].nunique() < 2 and out["closing_hour"].iloc[0] == 23:
        out["closing_hour"] = 23

    out["log_visitor"] = np.log1p(out["visitor_count"].astype(float))

    facilities = out["facilities"].fillna("").astype(str)
    out["facility_count"] = facilities.map(lambda s: len([x for x in s.split("|") if x]) if s else 0)
    out["has_parking"] = facilities.str.contains("parkir").astype(int)
    out["has_food"] = facilities.str.contains("makan|homestay").astype(int)
    out["has_guide"] = facilities.str.contains("guide|pemandu").astype(int)
    out["has_camping"] = facilities.str.contains("camping").astype(int)
    out["has_wifi"] = facilities.str.contains("wifi").astype(int)

    for col in ["review_count", "price_min", "popularity", "visitor_count"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(float)

    return out


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = _default_feature_df(df.to_dict("records"))
    df = engineer_features(df)
    if TARGET not in df.columns:
        raise ValueError(f"Dataset must contain '{TARGET}' column")
    df = df.dropna(subset=[TARGET])
    return df


def train_model(df: pd.DataFrame, model_dir: Path, n_estimators: int = 300, max_depth: int = 14) -> dict[str, Any]:
    X = df[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS].copy()
    y = df[TARGET].astype(float)

    label_encoders: dict[str, LabelEncoder] = {}
    for col in CATEGORICAL_COLUMNS:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le

    feature_columns = list(X.columns)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=1 - settings.ML_TRAIN_SPLIT, random_state=RNG_SEED
    )

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=RNG_SEED,
        oob_score=True,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    # bucket accuracy (+-5, +-10, +-15)
    buckets = {
        "within_5": float(np.mean(np.abs(y_pred - y_test.values) <= 5)),
        "within_10": float(np.mean(np.abs(y_pred - y_test.values) <= 10)),
        "within_15": float(np.mean(np.abs(y_pred - y_test.values) <= 15)),
    }

    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "hidden_gem_model.joblib")
    joblib.dump(scaler, model_dir / "scaler.joblib")
    joblib.dump(label_encoders, model_dir / "label_encoders.joblib")
    joblib.dump(feature_columns, model_dir / "feature_columns.joblib")

    feature_importance = dict(zip(feature_columns, (model.feature_importances_ * 100).round(2)))

    artifacts = {
        "status": "success",
        "model_path": str(model_dir / "hidden_gem_model.joblib"),
        "samples": int(len(df)),
        "features": len(feature_columns),
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "r2": round(r2, 4),
        "oob_score": round(float(model.oob_score_), 4),
        "accuracy_buckets": {k: round(v, 4) for k, v in buckets.items()},
        "feature_importance": feature_importance,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_estimators": n_estimators,
    }

    meta_path = model_dir / "model_metadata.json"
    meta_path.write_text(json.dumps(artifacts, indent=2), encoding="utf-8")
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="app/ml/data/destinations.csv")
    parser.add_argument("--output", default=str(Path(settings.ML_MODEL_PATH).parent))
    parser.add_argument("--estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=14)
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Dataset not found: {data_path}")
        print("Generate it first with: python scripts/generate_dataset.py")
        raise SystemExit(1)

    df = load_dataset(data_path)
    print(f"Loaded {len(df)} samples, target: {TARGET}")
    artifacts = train_model(df, Path(args.output), args.estimators, args.max_depth)
    print(json.dumps({k: v for k, v in artifacts.items() if k != "feature_importance"}, indent=2))
    print("Training complete.")


if __name__ == "__main__":
    main()
