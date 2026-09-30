"""
Generates a synthetic placeholder Energy dataset so the dashboard has
real rows to show out of the box.

HONESTY NOTE: unlike Maintenance (real NASA C-MAPSS data, recoverable
from data/raw_maintenance) and Security (data/build_security_dataset.py,
already synthetic-by-design and documented as such), this handout's zip
did not include the original build_energy_dataset.py or its real source
data, so there's nothing genuine left to recover here. This script
fabricates a plausible-shaped dataset (daily HVAC-driven load curve,
weekday/weekend difference, a few injected anomaly spikes) purely so the
Energy dashboard and its ML models have SOMETHING to run against — it is
NOT the original dataset, and the bundled forecast models
(ml_models/energy/*.pkl) were trained on the real one, so forecast
accuracy/confidence numbers shown against this placeholder data should
not be taken as representative. Replace this file's output with real
data (or a real script) as soon as one is available.

Usage:
    cd backend && python data/build_energy_dataset.py
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw"
BUILDING_ID = "BLD-HQ-01"
DAYS = 120


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.RandomState(42)

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(days=DAYS)
    timestamps = pd.date_range(start, now, freq="h")

    rows = []
    for ts in timestamps:
        hour, weekday = ts.hour, ts.weekday()
        is_business_hours = 8 <= hour <= 18
        is_weekend = weekday >= 5
        occupancy_factor = (0.3 if is_weekend else 1.0) * (1.0 if is_business_hours else 0.35)

        hvac = 18 + 14 * occupancy_factor + rng.normal(0, 1.5)
        lighting = 6 + 5 * occupancy_factor + rng.normal(0, 0.6)
        plug_load = 8 + 10 * occupancy_factor + rng.normal(0, 1.2)
        other = 4 + rng.normal(0, 0.5)

        # Rare anomaly spikes (~1.5% of hours) — equipment left running,
        # so the drift/anomaly detectors have something real to flag.
        if rng.random() < 0.015:
            hvac *= rng.uniform(1.6, 2.2)

        hvac, lighting, plug_load, other = (max(0.0, v) for v in (hvac, lighting, plug_load, other))
        rows.append({
            "building_id": BUILDING_ID, "sensor_id": "MAIN", "timestamp": ts.isoformat(),
            "total_kwh": round(hvac + lighting + plug_load + other, 2),
            "hvac_kwh": round(hvac, 2), "lighting_kwh": round(lighting, 2),
            "plug_load_kwh": round(plug_load, 2), "other_kwh": round(other, 2),
        })

    df = pd.DataFrame(rows)
    df.to_csv(RAW_DIR / "energy_readings_raw.csv", index=False)
    print(f"Wrote {len(df)} hourly readings to {RAW_DIR / 'energy_readings_raw.csv'}")


if __name__ == "__main__":
    main()
