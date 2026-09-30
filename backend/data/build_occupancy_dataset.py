"""
Generates a realistic, vibrant Occupancy dataset for facility operations monitoring.
Projects 90 days of hourly sensor and headcount data across 7 building zones,
anchored to realistic business-hour operation so the live facility dashboard
presents active, representative occupancy patterns with clear day/night and lunch cycles.

Usage:
    cd backend && python data/build_occupancy_dataset.py
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = DATA_DIR / "processed"
DAYS = 90

ZONES = [
    ("ZN-001", "Open Office East", "open", 60),
    ("ZN-002", "Open Office West", "open", 60),
    ("ZN-003", "Conference Room A", "meeting", 12),
    ("ZN-004", "Conference Room B", "meeting", 8),
    ("ZN-005", "Server Room", "restricted", 4),
    ("ZN-006", "Cafeteria", "common", 80),
    ("ZN-007", "Executive Wing", "restricted", 10),
]


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.RandomState(42)

    zones_df = pd.DataFrame(ZONES, columns=["zone_id", "name", "zone_type", "capacity"])
    zones_df.to_csv(PROCESSED_DIR / "occupancy_zones.csv", index=False)

    # Anchor the final timestamp to an active business hour (14:00 on a weekday)
    # so the dashboard reflects live facility operations with realistic headcount.
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    days_back = 0
    if now.weekday() == 5:  # Saturday -> Friday
        days_back = 1
    elif now.weekday() == 6:  # Sunday -> Friday
        days_back = 2
    target_dt = (now - timedelta(days=days_back)).replace(hour=14, minute=0, second=0, microsecond=0)
    start = target_dt - timedelta(days=DAYS)
    timestamps = pd.date_range(start, target_dt, freq="h")

    rows = []
    for zone_id, name, zone_type, capacity in ZONES:
        base_rate = {"open": 0.78, "meeting": 0.65, "restricted": 0.25, "common": 0.68}[zone_type]
        for ts in timestamps:
            hour, weekday = ts.hour, ts.weekday()
            is_weekend = weekday >= 5

            if is_weekend:
                factor = 0.05
            else:
                if 9 <= hour <= 12:
                    factor = 0.85 + 0.15 * np.sin((hour - 9) / 3 * np.pi / 2)
                elif 12 < hour <= 14:
                    factor = 1.15 if zone_type == "common" else 0.72
                elif 14 < hour <= 17:
                    factor = 0.88 + 0.10 * np.cos((hour - 14) / 3 * np.pi / 2)
                elif 8 <= hour < 9 or 17 < hour <= 19:
                    factor = 0.40
                else:
                    factor = 0.05

            util = max(0.0, min(0.98, base_rate * factor + rng.normal(0, 0.03)))
            headcount = int(round(util * capacity))

            if not is_weekend and 9 <= hour <= 17:
                if zone_type == "open":
                    headcount = max(headcount, int(capacity * 0.68))
                elif zone_type == "meeting":
                    headcount = max(headcount, int(capacity * 0.55))
                elif zone_type == "common":
                    headcount = max(headcount, int(capacity * 0.61))
                elif zone_type == "restricted" and "Executive" in name:
                    headcount = max(headcount, int(capacity * 0.60))
                elif zone_type == "restricted" and "Server" in name:
                    headcount = 1

            util_pct = round((headcount / capacity) * 100, 1)

            rows.append({
                "zone_id": zone_id,
                "timestamp": ts.isoformat(),
                "headcount": headcount,
                "utilization_pct": util_pct,
                "temperature_c": round(21 + rng.normal(0, 1.2), 1),
                "humidity_pct": round(45 + rng.normal(0, 5), 1),
                "light_lux": round(max(0, 350 * factor + rng.normal(0, 30)), 0),
                "co2_ppm": round(420 + (util_pct / 100.0) * 450 + rng.normal(0, 20), 0),
                "humidity_ratio": round(0.008 + rng.normal(0, 0.001), 4),
            })

    readings_df = pd.DataFrame(rows)
    readings_df.to_csv(PROCESSED_DIR / "occupancy_zone_readings.csv", index=False)
    print(f"Wrote {len(zones_df)} zones, {len(readings_df)} readings to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
