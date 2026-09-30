"""
Recreates backend/data/processed/maintenance_assets.csv and
maintenance_fleet_readings.csv from the bundled NASA C-MAPSS raw data
(data/raw_maintenance/train_FD001.txt) — these two processed CSVs are
what maintenance_service.ingest_fleet() actually reads, but weren't
included in this handout's zip export (only the raw NASA files and the
already-trained model artifacts were). The exact 8-sensor rename mapping
below is copied verbatim from ml_models/maintenance/train_health_model.py
and train_lstm_rul_model.py's own RAW_RENAME (both already correctly
recover from just the raw NASA files, so this is the proven-correct
mapping the live models were actually trained against) — this script
does the same conversion for the "live fleet" (the TRAIN_FD001 engines,
which is exactly what the original CMMS-integration story pretends is
"the current fleet") rather than for held-out evaluation.

Each of the 100 training engines becomes one Asset; each (engine, cycle)
row becomes one AssetReading, with `cycle` mapped onto a real timestamp
(1 cycle = 1 day, most recent cycle = now) so the live dashboard's
"latest reading" reads as current rather than as a multi-decade-old log.

Usage:
    cd backend && python data/build_maintenance_dataset.py
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw_maintenance"
PROCESSED_DIR = DATA_DIR / "processed"
BUILDING_ID = "BLD-HQ-01"

COLS_RAW = ["unit_nr", "cycle", "setting1", "setting2", "setting3"] + [f"s{i}" for i in range(1, 22)]
RAW_RENAME = {
    "s2": "temp_stage1_c", "s3": "temp_stage2_c", "s4": "temp_stage3_c",
    "s7": "pressure_kpa", "s11": "vibration_index", "s12": "flow_rate",
    "s15": "efficiency_ratio", "s21": "bleed_load",
}

# 100 training engines get cycled across a handful of plausible HVAC
# asset types/locations so the fleet reads as a real mixed building
# plant, not 100 identical "Engine N" rows.
ASSET_TYPES = [
    ("Chiller", "Mechanical Room {n}"), ("Air Handling Unit", "Floor {n} Plant Room"),
    ("Cooling Tower", "Rooftop"), ("Boiler", "Mechanical Room {n}"),
    ("Pump Set", "Basement Utility {n}"),
]


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(RAW_DIR / "train_FD001.txt", sep=r"\s+", header=None, names=COLS_RAW)
    raw = raw.rename(columns=RAW_RENAME)[["unit_nr", "cycle"] + list(RAW_RENAME.values())]

    unit_ids = sorted(raw["unit_nr"].unique())
    rng = __import__("numpy").random.RandomState(11)
    assets = []
    for i, unit_nr in enumerate(unit_ids):
        asset_type, location_tmpl = ASSET_TYPES[i % len(ASSET_TYPES)]
        assets.append({
            "building_id": BUILDING_ID,
            "asset_id": f"AST-{unit_nr:03d}",
            "name": f"{asset_type} {unit_nr:03d}",
            "asset_type": asset_type,
            "location": location_tmpl.format(n=(i % 6) + 1),
        })
    assets_df = pd.DataFrame(assets)
    assets_df.to_csv(PROCESSED_DIR / "maintenance_assets.csv", index=False)

    # The train_FD001 engines each run all the way to failure — using a
    # full trajectory as "the current fleet's latest reading" would mean
    # EVERY asset looks like it's about to fail, which isn't realistic
    # for a live fleet snapshot. Instead, truncate each engine's history
    # at a random point (60-98% of its full life) the same way NASA's own
    # test_FD001 set is built, so the live fleet shows a real mix of
    # healthy/warning/critical assets instead of ~100 simultaneous
    # near-failures.
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    readings = []
    for unit_nr in unit_ids:
        eng = raw[raw["unit_nr"] == unit_nr].sort_values("cycle")
        full_life = eng["cycle"].max()
        cutoff = max(20, int(full_life * rng.uniform(0.60, 0.98)))
        eng = eng[eng["cycle"] <= cutoff]
        max_cycle = eng["cycle"].max()
        for row in eng.itertuples(index=False):
            ts = now - timedelta(days=int(max_cycle - row.cycle))
            readings.append({
                "asset_id": f"AST-{unit_nr:03d}", "cycle": row.cycle, "timestamp": ts.isoformat(),
                "temp_stage1_c": row.temp_stage1_c, "temp_stage2_c": row.temp_stage2_c,
                "temp_stage3_c": row.temp_stage3_c, "pressure_kpa": row.pressure_kpa,
                "vibration_index": row.vibration_index, "flow_rate": row.flow_rate,
                "efficiency_ratio": row.efficiency_ratio, "bleed_load": row.bleed_load,
            })
    readings_df = pd.DataFrame(readings)
    readings_df.to_csv(PROCESSED_DIR / "maintenance_fleet_readings.csv", index=False)

    print(f"Wrote {len(assets_df)} assets, {len(readings_df)} readings to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
