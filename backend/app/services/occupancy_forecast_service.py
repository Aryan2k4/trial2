"""
Live inference for the zone utilization forecast (see
ml_models/occupancy/train_utilization_forecast.py for training/why this
model exists). This is what makes Occupancy's forecast a genuinely-used
model rather than a training-time report: given a zone's readings
currently in the DB (bundled dataset, or whatever CSV someone uploaded
through /occupancy/ingest/upload), predicts that zone's utilization ~1
hour ahead — recomputed fresh on every call from whatever's actually
loaded right now.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.utils.drift_detection import compute_drift

MODEL_DIR = Path(__file__).resolve().parents[2] / "ml_models" / "occupancy"
MODEL_PATH = MODEL_DIR / "utilization_forecast_model.pkl"
METRICS_PATH = MODEL_DIR / "forecast_model_metrics.json"

_cache = {}


def is_available() -> bool:
    return MODEL_PATH.exists()


def _load_model():
    if "bundle" not in _cache:
        _cache["bundle"] = joblib.load(MODEL_PATH)
    return _cache["bundle"]


def get_confidence() -> dict:
    if not METRICS_PATH.exists():
        return {"available": False}
    metrics = json.loads(METRICS_PATH.read_text())
    best = metrics["all_models"][metrics["best_model"]]
    improvement = metrics["improvement_over_best_naive_pct"]
    confidence = "high" if improvement >= 20 else "medium" if improvement >= 8 else "low"
    return {
        "available": True,
        "model_used": metrics["best_model"],
        "mae_pct": best["held_out_test_mae_pct"],
        "r2": best["held_out_test_r2"],
        "improvement_over_naive_pct": improvement,
        "confidence": confidence,
        "horizon_minutes": metrics.get("horizon_minutes", 60),
    }


def get_data_drift(readings_df: pd.DataFrame, capacity: float) -> dict:
    """Does the CURRENT zone data still look like what this forecast model
    was trained on — see app/utils/drift_detection.py."""
    if not METRICS_PATH.exists() or readings_df.empty:
        return {"available": False}
    metrics = json.loads(METRICS_PATH.read_text())
    training_dist = metrics.get("training_distribution")
    if not training_dist:
        return {"available": False}
    current_means = {
        "util_now": float(readings_df["utilization_pct"].mean()),
        "capacity": float(capacity) if capacity is not None else None,
    }
    return compute_drift(current_means, training_dist)


def forecast_zone_utilization(readings_df: pd.DataFrame, zone_type: str, capacity: int) -> dict:
    """readings_df: this zone's reading history (timestamp, headcount,
    utilization_pct), ANY length >= 1 — shorter history degrades feature
    quality gracefully (rolling/lag features fall back to the latest known
    value) rather than refusing to predict, since a freshly-uploaded zone
    with little history yet is a normal, expected case, not an error."""
    if not is_available():
        return {"available": False, "reason": "model_not_trained"}
    if readings_df.empty:
        return {"available": False, "reason": "no_readings"}

    bundle = _load_model()
    model, features = bundle["model"], bundle["features"]

    work = readings_df.sort_values("timestamp").reset_index(drop=True).copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"])
    latest = work.iloc[-1]
    hour, dow = latest["timestamp"].hour, latest["timestamp"].dayofweek

    trailing_4h = work.tail(16)
    yesterday_idx = len(work) - 1 - 24 * 4
    last_week_idx = len(work) - 1 - 7 * 24 * 4
    util_now = float(latest["utilization_pct"])

    row = {
        "hour": hour, "day_of_week": dow, "is_weekend": int(dow >= 5),
        "hour_sin": np.sin(2 * np.pi * hour / 24), "hour_cos": np.cos(2 * np.pi * hour / 24),
        "dow_sin": np.sin(2 * np.pi * dow / 7), "dow_cos": np.cos(2 * np.pi * dow / 7),
        "capacity": capacity or 0,
        "util_now": util_now,
        "util_rolling_mean_4h": float(trailing_4h["utilization_pct"].mean()),
        "util_rolling_std_4h": float(trailing_4h["utilization_pct"].std()) if len(trailing_4h) > 1 else 0.0,
        "util_same_hour_yesterday": float(work.iloc[yesterday_idx]["utilization_pct"]) if yesterday_idx >= 0 else util_now,
        "util_same_hour_last_week": float(work.iloc[last_week_idx]["utilization_pct"]) if last_week_idx >= 0 else util_now,
        "is_workspace": int(zone_type == "workspace"), "is_meeting_room": int(zone_type == "meeting_room"),
        "is_common_area": int(zone_type == "common_area"), "is_restricted": int(zone_type == "restricted"),
    }
    X = pd.DataFrame([row])[features].fillna(0)
    predicted = float(np.clip(model.predict(X)[0], 0, 100))
    forecast_time = latest["timestamp"] + pd.Timedelta(minutes=bundle["horizon_steps"] * 15)

    return {
        "available": True,
        "current_utilization_pct": round(util_now, 1),
        "current_timestamp": latest["timestamp"],
        "predicted_utilization_pct": round(predicted, 1),
        "predicted_timestamp": forecast_time,
        "model_used": bundle["model_name"],
        "confidence": get_confidence(),
        "data_drift": get_data_drift(work, capacity),
    }
