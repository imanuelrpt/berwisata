"""
ML inference service. Loads serialized artifacts once and exposes:
    - predict_score(destination-like dict) -> hidden gem score
    - rank_by_model(candidates, preferences) -> model-informed ranking
    - fallback heuristic scoring when model file is absent
"""
import json
import logging
import threading
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np

from app.core.config import settings
from app.ml.train import CATEGORICAL_COLUMNS, NUMERIC_COLUMNS, engineer_features

logger = logging.getLogger("app.ml_service")

FALLBACK_WEIGHTS = {
    "rating": 0.25,
    "review_ratio": 0.20,
    "visitor_ratio": 0.20,
    "beauty": 0.20,
    "access": 0.15,
}

_model: Optional[Any] = None
_scaler: Optional[Any] = None
_label_encoders: Optional[dict] = None
_feature_columns: Optional[list[str]] = None
_lock = threading.Lock()


def _model_dir() -> Path:
    return Path(settings.ML_MODEL_PATH).parent


def model_available() -> bool:
    return (_model_dir() / "hidden_gem_model.joblib").exists()


def _load_model() -> None:
    global _model, _scaler, _label_encoders, _feature_columns
    if _model is not None:
        return
    with _lock:
        if _model is not None:
            return
        model_path = Path(settings.ML_MODEL_PATH)
        scaler_path = Path(settings.ML_SCALER_PATH)
        enc_path = Path(settings.ML_ENCODER_PATH)
        feat_path = Path(settings.ML_FEATURES_PATH)
        if model_path.exists() and scaler_path.exists():
            _model = joblib.load(model_path)
            _scaler = joblib.load(scaler_path)
            _label_encoders = joblib.load(enc_path) if enc_path.exists() else None
            _feature_columns = joblib.load(feat_path) if feat_path.exists() else None
            logger.info("ML model loaded from %s", model_path)
        else:
            logger.warning("ML model not found, using fallback heuristic scoring")


def reload_model() -> bool:
    global _model, _scaler, _label_encoders, _feature_columns
    with _lock:
        _model = _scaler = _label_encoders = _feature_columns = None
    _load_model()
    return model_available()


def predict_scores(rows: list[dict]) -> list[float]:
    """Predict hidden gem score for a list of destination-like dicts (0-100)."""
    if not rows:
        return []
    _load_model()
    if _model is None or _scaler is None:
        return [_fallback_score(r) for r in rows]

    import pandas as pd

    df = pd.DataFrame(rows)
    try:
        df = engineer_features(df)
        df = df[_feature_columns].copy()
        for col in CATEGORICAL_COLUMNS:
            if col in _label_encoders:
                le = _label_encoders[col]
                df[col] = df[col].astype(str).map(
                    lambda v: le.transform([v])[0] if v in le.classes_ else -1
                )
        X = _scaler.transform(df.astype(float))
        preds = _model.predict(X)
        return [round(float(max(0.0, min(100.0, p))), 2) for p in preds]
    except Exception as exc:  # pragma: no cover - resilience path
        logger.exception("ML prediction failed, falling back: %s", exc)
        return [_fallback_score(r) for r in rows]


def predict_score(row: dict) -> float:
    scores = predict_scores([row])
    return scores[0]


def _fallback_score(row: dict) -> float:
    rating = float(row.get("rating", 4.0))
    review = float(row.get("review_count", 0))
    visitors = float(row.get("visitor_count", 0))
    beauty = float(row.get("beauty", 4.0))
    road = float(row.get("road_access", 3.0))
    crowd = float(row.get("crowd_level", 3.0))

    review_ratio = min(review / 5000.0, 1.0)
    visitor_ratio = min(visitors / 1_000_000.0, 1.0)

    raw = (
        FALLBACK_WEIGHTS["rating"] * (rating / 5.0) * 100
        + FALLBACK_WEIGHTS["review_ratio"] * (1.0 - review_ratio) * 100
        + FALLBACK_WEIGHTS["visitor_ratio"] * (1.0 - visitor_ratio) * 100
        + FALLBACK_WEIGHTS["beauty"] * (beauty / 5.0) * 100
        + FALLBACK_WEIGHTS["access"] * (road / 5.0) * 100
        - (crowd - 3.0) * 3.0
    )
    return round(max(0.0, min(100.0, raw)), 2)


def rank_candidates(candidates: list[dict], preference_boost: Optional[dict] = None) -> list[dict]:
    """Rank candidates by predicted hidden gem score with optional preference boost."""
    preference_boost = preference_boost or {}
    for c in candidates:
        base = predict_score(c)
        boost = 0.0
        cat = c.get("category", "")
        if cat in preference_boost:
            boost = float(preference_boost[cat]) * 8.0
        if c.get("crowd_level", 3) >= 4.5 and preference_boost.get("not_crowded"):
            base *= 0.85
        c["_ml_score"] = round(max(0.0, min(100.0, base + boost)), 2)
    return sorted(candidates, key=lambda x: x["_ml_score"], reverse=True)


def training_metadata() -> Optional[dict]:
    meta = _model_dir() / "model_metadata.json"
    if meta.exists():
        return json.loads(meta.read_text(encoding="utf-8"))
    return None
