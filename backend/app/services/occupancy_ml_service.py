"""
Live classification of REAL zone readings, using the classical UCI-trained
Occupied/Empty model (ml_models/occupancy/occupancy_model.pkl).

PREVIOUSLY, this project's occupancy classifiers (classical + CNN) only
ever evaluated their own fixed, pre-computed held-out test samples
(cnn_live_samples.json) — genuinely useful for an honest offline accuracy
report, but they never touched whatever was actually sitting in the
ZoneReading table, unlike every other domain's live models. That gap
existed because ZoneReading only stored headcount/utilization_pct — none
of the Temperature/Humidity/Light/CO2/HumidityRatio columns the
classifier was trained on. Both the DB model and the upload endpoint were
extended (see app/models/occupancy_models.py's new nullable environmental
columns, and occupancy_routes.py's OCCUPANCY_ALIASES) so a zone that
actually has these readings — e.g. via an uploaded CSV shaped like the
UCI dataset itself — can be classified for real.

A zone with no environmental readings yet (the bundled dataset's own
headcount-only zones) simply has nothing to classify — `available: False`
in the response, not a crash or a fake number.
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from app.models.occupancy_models import Zone, ZoneReading
from app.utils.drift_detection import compute_drift

MODEL_DIR = Path(__file__).resolve().parents[2] / "ml_models" / "occupancy"
MODEL_PATH = MODEL_DIR / "occupancy_model.pkl"
METRICS_PATH = MODEL_DIR / "model_metrics.json"

ENV_COL_MAP = {
    "Temperature": "temperature_c", "Humidity": "humidity_pct",
    "Light": "light_lux", "CO2": "co2_ppm", "HumidityRatio": "humidity_ratio",
}

_bundle_cache = None


def _load_model():
    global _bundle_cache
    if _bundle_cache is None:
        _bundle_cache = joblib.load(MODEL_PATH)
    return _bundle_cache


def classify_zone(db: Session, zone_id: str) -> dict:
    """Classifies a zone's MOST RECENT reading that actually has
    environmental data, using the real trained model — not a replay."""
    zone = db.query(Zone).filter(Zone.zone_id == zone_id).first()
    if zone is None:
        return {"available": False, "reason": f"Unknown zone_id '{zone_id}'."}

    latest = (
        db.query(ZoneReading)
        .filter(ZoneReading.zone_id == zone_id, ZoneReading.temperature_c.isnot(None))
        .order_by(ZoneReading.timestamp.desc())
        .first()
    )
    if latest is None:
        return {
            "available": False,
            "reason": (
                "This zone has no environmental-sensor readings (Temperature/Humidity/Light/CO2/HumidityRatio) "
                "yet — only headcount. Upload a CSV with those columns (see /occupancy/ingest/upload) to enable "
                "live classification for this zone."
            ),
        }

    bundle = _load_model()
    model, features = bundle["model"], bundle["features"]
    row = {
        "Temperature": latest.temperature_c, "Humidity": latest.humidity_pct,
        "Light": latest.light_lux, "CO2": latest.co2_ppm, "HumidityRatio": latest.humidity_ratio,
    }
    X = pd.DataFrame([row])[features]
    predicted_occupied = bool(model.predict(X)[0])
    proba = float(model.predict_proba(X)[0][1]) if hasattr(model, "predict_proba") else None

    # Cross-check against the zone's OWN reported headcount, if this
    # reading also has one — two independently-derived signals agreeing
    # (or not) is more informative than either alone, same "don't trust
    # one signal blindly" philosophy as the cross-domain investigation
    # agent's correlation checks.
    headcount_says_occupied = latest.headcount > 0
    agrees_with_headcount = predicted_occupied == headcount_says_occupied

    training_dist = {}
    if METRICS_PATH.exists():
        training_dist = json.loads(METRICS_PATH.read_text()).get("training_distribution", {})
    current_means = {ENV_COL_MAP[k]: v for k, v in row.items() if v is not None and ENV_COL_MAP[k] in training_dist}
    # compute_drift expects keys matching training_dist's own keys
    # (Temperature/Humidity/... as saved), so map back.
    reverse_map = {v: k for k, v in ENV_COL_MAP.items()}
    current_means_for_drift = {reverse_map.get(k, k): v for k, v in current_means.items()}
    drift = compute_drift(current_means_for_drift, training_dist) if training_dist else {"available": False}

    return {
        "available": True,
        "zone_id": zone_id,
        "zone_name": zone.name,
        "reading_timestamp": latest.timestamp,
        "predicted_occupied": predicted_occupied,
        "confidence_pct": round(proba * 100, 1) if proba is not None else None,
        "model_used": bundle.get("model_name"),
        "reported_headcount": latest.headcount,
        "agrees_with_reported_headcount": agrees_with_headcount,
        "data_drift": drift,
    }
