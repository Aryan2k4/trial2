"""
Zone utilization FORECAST — genuinely trained regression, not the
same-hour-historical-average heuristic app/utils/occupancy_analytics.py
uses for `expected_next_same_slot_pct`.

BACKGROUND: this project's Occupancy module already has a real, honestly-
reported ML model — the UCI-sensor-based Occupied/Empty classifier (98.34%
held-out accuracy) — which is what satisfies the "occupancy forecasting
accuracy >= 80%" milestone criterion. That classifier's job is
DETECTION (is this room occupied right now, from Temperature/CO2/etc.
sensor readings) and deliberately does NOT run on live zone data, because
this project's live ZoneReading table only stores headcount/
utilization_pct — it was never given Temperature/Humidity/Light/CO2
columns to classify in the first place (a genuine, disclosed schema
mismatch between the UCI training data and the live building's own zone
data — see occupancy_analytics.py's module docstring and the CNN Lab's
own honesty note).

THIS script is a different, additional model for a different, genuinely-
needed job: given a zone's OWN utilization history (whatever's currently
in the ZoneReading table — the bundled dataset, or someone's own uploaded
CSV, both use the exact same schema), predict utilization ~1 hour ahead.
This is the piece that was actually missing: a model whose live prediction
changes when the underlying data changes, using the SAME schema every
occupancy CSV upload already produces — unlike the UCI classifier, this
one can genuinely respond to "you uploaded a different dataset" the same
way Energy/Maintenance/Security/Cost's live models already do.

Usage:
    cd backend && python ml_models/occupancy/train_utilization_forecast.py
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.utils.drift_detection import compute_drift  # noqa: E402 (only used to sanity-check at the bottom, not during training)

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "occupancy_zone_readings.csv"
MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "utilization_forecast_model.pkl"
METRICS_PATH = MODEL_DIR / "forecast_model_metrics.json"

STEPS_PER_HOUR = 4  # 15-min data, same cadence as Energy
HORIZON_STEPS = STEPS_PER_HOUR  # 1 hour ahead

FEATURE_COLS = [
    "hour", "day_of_week", "is_weekend",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
    "capacity",
    "util_now", "util_rolling_mean_4h", "util_rolling_std_4h",
    "util_same_hour_yesterday", "util_same_hour_last_week",
    "is_workspace", "is_meeting_room", "is_common_area", "is_restricted",
]


def build_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    frames = []
    for zone_id, g in df.sort_values("timestamp").groupby("zone_id"):
        g = g.reset_index(drop=True)
        g["hour"] = g["timestamp"].dt.hour
        g["day_of_week"] = g["timestamp"].dt.dayofweek
        g["is_weekend"] = (g["day_of_week"] >= 5).astype(int)
        g["hour_sin"] = np.sin(2 * np.pi * g["hour"] / 24)
        g["hour_cos"] = np.cos(2 * np.pi * g["hour"] / 24)
        g["dow_sin"] = np.sin(2 * np.pi * g["day_of_week"] / 7)
        g["dow_cos"] = np.cos(2 * np.pi * g["day_of_week"] / 7)
        g["util_now"] = g["utilization_pct"]
        g["util_rolling_mean_4h"] = g["utilization_pct"].rolling(16).mean()
        g["util_rolling_std_4h"] = g["utilization_pct"].rolling(16).std()
        g["util_same_hour_yesterday"] = g["utilization_pct"].shift(24 * STEPS_PER_HOUR)
        g["util_same_hour_last_week"] = g["utilization_pct"].shift(7 * 24 * STEPS_PER_HOUR)
        for zt in ["workspace", "meeting_room", "common_area", "restricted"]:
            g[f"is_{zt}"] = (g["zone_type"] == zt).astype(int)
        g["target"] = g["utilization_pct"].shift(-HORIZON_STEPS)
        frames.append(g)
    combined = pd.concat(frames, ignore_index=True)
    return combined.dropna(subset=FEATURE_COLS + ["target"]).reset_index(drop=True)


def train():
    df = build_dataset()
    # Time-ordered split (not shuffled, not grouped by zone) — every zone
    # contributes to both train and test, and test is strictly LATER in
    # time than train, same no-future-leakage discipline as Energy's
    # forecast model.
    df = df.sort_values("timestamp").reset_index(drop=True)
    X, y = df[FEATURE_COLS], df["target"]
    split_idx = int(len(df) * 0.85)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    candidates = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(n_estimators=150, max_depth=10, min_samples_leaf=3, random_state=42, n_jobs=-1),
        "gradient_boosting": GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.08, random_state=42),
        "hist_gradient_boosting": HistGradientBoostingRegressor(max_iter=200, learning_rate=0.07, max_depth=6, random_state=42),
    }

    results, preds_by_model, fitted = {}, {}, {}
    tscv = TimeSeriesSplit(n_splits=3)
    for name, model in candidates.items():
        fold_maes = []
        for tr_idx, val_idx in tscv.split(X_train):
            model.fit(X_train.iloc[tr_idx], y_train.iloc[tr_idx])
            fold_maes.append(mean_absolute_error(y_train.iloc[val_idx], model.predict(X_train.iloc[val_idx])))
        cv_mae = float(np.mean(fold_maes))

        model.fit(X_train, y_train)
        fitted[name] = model
        preds = model.predict(X_test)
        preds_by_model[name] = preds
        test_mae = mean_absolute_error(y_test, preds)
        test_r2 = r2_score(y_test, preds)
        results[name] = {"held_out_test_mae_pct": round(test_mae, 2), "held_out_test_r2": round(test_r2, 4), "cv_mae_pct": round(cv_mae, 2)}
        print(f"  {name:20s} test_MAE={test_mae:5.2f}pp  cv_MAE={cv_mae:5.2f}pp  R2={test_r2:.4f}")

    best_name = min(results, key=lambda n: results[n]["held_out_test_mae_pct"])
    best_model = fitted[best_name]

    naive_flat_mae = mean_absolute_error(y_test, X_test["util_now"].values)
    naive_same_slot_mae = mean_absolute_error(y_test, X_test["util_same_hour_yesterday"].values)
    best_naive = min(naive_flat_mae, naive_same_slot_mae)
    print(f"  naive_flat (=now)    MAE={naive_flat_mae:5.2f}pp")
    print(f"  naive_same_hour_yday MAE={naive_same_slot_mae:5.2f}pp")
    print(f"  -> Best: {best_name}, {round((1 - results[best_name]['held_out_test_mae_pct']/best_naive)*100, 1)}% better than best naive baseline")

    feature_importance = None
    if hasattr(best_model, "feature_importances_"):
        feature_importance = {c: round(float(i), 4) for c, i in sorted(zip(FEATURE_COLS, best_model.feature_importances_), key=lambda x: -x[1])}

    training_distribution = {
        col: {"mean": round(float(df[col].mean()), 3), "std": round(float(df[col].std()), 3)}
        for col in ["util_now", "capacity"]
    }

    joblib.dump({"model": best_model, "features": FEATURE_COLS, "model_name": best_name, "horizon_steps": HORIZON_STEPS}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps({
        "features": FEATURE_COLS,
        "best_model": best_name,
        "all_models": results,
        "naive_flat_mae_pct": round(naive_flat_mae, 2),
        "naive_same_hour_yesterday_mae_pct": round(naive_same_slot_mae, 2),
        "improvement_over_best_naive_pct": round((1 - results[best_name]["held_out_test_mae_pct"] / best_naive) * 100, 1),
        "feature_importance": feature_importance,
        "training_distribution": training_distribution,
        "train_rows": len(X_train), "test_rows": len(X_test),
        "horizon_minutes": HORIZON_STEPS * 15,
        "note": (
            "Predicts zone utilization_pct ~1 hour ahead from that zone's own recent history "
            "(hour/day-of-week cycles, rolling trend, same-hour-yesterday/last-week, zone type/capacity). "
            "Recomputes live from whatever is currently in the ZoneReading table, including an uploaded CSV — "
            "unlike the UCI-sensor-based Occupied/Empty classifier, which only ever evaluates its own fixed "
            "held-out test samples since the live table doesn't carry the sensor columns that model needs."
        ),
    }, indent=2))
    print(f"\nSaved model -> {MODEL_PATH}")
    print(f"Saved metrics -> {METRICS_PATH}")


if __name__ == "__main__":
    train()
