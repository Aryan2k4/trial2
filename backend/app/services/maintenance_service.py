"""
Maintenance data service.

Two responsibilities:
1. Ingest the live fleet dataset (backend/data/build_maintenance_dataset.py
   output) into Asset / AssetReading — same "file-as-stand-in-for-a-real-
   feed" seam as the Energy module's data_service (swap for a real BACnet/
   CMMS/IoT connector in production without touching anything downstream).
2. open_work_order() — the REAL implementation behind maintenance alerts.
   This is deliberately the single function both the Maintenance Agent's
   own tools AND the Energy Agent's flag_for_maintenance_review call, so
   the Energy→Maintenance cross-agent handoff creates one actual row in the
   same table regardless of which agent triggered it.
"""
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.maintenance_models import Asset, AssetReading, MaintenanceEvent

DEFAULT_BUILDING_ID = "BLD-HQ-01"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
FLEET_CSV = PROCESSED_DIR / "maintenance_fleet_readings.csv"
ASSETS_CSV = PROCESSED_DIR / "maintenance_assets.csv"


# ---- Ingestion -------------------------------------------------------

def ingest_fleet(db: Session, fleet_csv: Path = FLEET_CSV, assets_csv: Path = ASSETS_CSV) -> dict:
    """(Re)loads the live fleet (assets + their sensor readings) from the
    processed CSVs. Idempotent-ish for demo purposes, same pattern as
    data_service.ingest_from_csv: clears existing rows before reloading."""
    if not fleet_csv.exists() or not assets_csv.exists():
        raise FileNotFoundError(
            f"Maintenance dataset not built yet. Run: "
            f"python data/build_maintenance_dataset.py (looked for {fleet_csv})"
        )

    assets_df = pd.read_csv(assets_csv)
    readings_df = pd.read_csv(fleet_csv, parse_dates=["timestamp"])

    db.query(AssetReading).delete()
    db.query(Asset).delete()

    asset_rows = [
        Asset(
            building_id=row.building_id,
            asset_id=row.asset_id,
            name=row.name,
            asset_type=row.asset_type,
            location=row.location,
            commissioned_at=None,
        )
        for row in assets_df.itertuples(index=False)
    ]
    db.bulk_save_objects(asset_rows)

    reading_rows = [
        AssetReading(
            asset_id=row.asset_id,
            cycle=int(row.cycle),
            timestamp=row.timestamp,
            temp_stage1_c=row.temp_stage1_c,
            temp_stage2_c=row.temp_stage2_c,
            temp_stage3_c=row.temp_stage3_c,
            pressure_kpa=row.pressure_kpa,
            vibration_index=row.vibration_index,
            flow_rate=row.flow_rate,
            efficiency_ratio=row.efficiency_ratio,
            bleed_load=row.bleed_load,
            true_rul_cycles=None,  # unknown for the live fleet — that's the ML task
        )
        for row in readings_df.itertuples(index=False)
    ]
    db.bulk_save_objects(reading_rows)
    db.commit()

    return {"assets_ingested": len(asset_rows), "readings_ingested": len(reading_rows)}


def has_data(db: Session, building_id: str = DEFAULT_BUILDING_ID) -> bool:
    count = db.query(func.count(Asset.id)).filter(Asset.building_id == building_id).scalar()
    return bool(count)


def list_assets(db: Session, building_id: str = DEFAULT_BUILDING_ID) -> list[Asset]:
    return db.query(Asset).filter(Asset.building_id == building_id).all()


def get_asset(db: Session, asset_id: str) -> Asset | None:
    return db.query(Asset).filter(Asset.asset_id == asset_id).first()


def get_readings_df(db: Session, asset_id: str) -> pd.DataFrame:
    rows = (
        db.query(
            AssetReading.cycle,
            AssetReading.timestamp,
            AssetReading.temp_stage1_c,
            AssetReading.temp_stage2_c,
            AssetReading.temp_stage3_c,
            AssetReading.pressure_kpa,
            AssetReading.vibration_index,
            AssetReading.flow_rate,
            AssetReading.efficiency_ratio,
            AssetReading.bleed_load,
        )
        .filter(AssetReading.asset_id == asset_id)
        .order_by(AssetReading.cycle)
        .all()
    )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=[
        "cycle", "timestamp", "temp_stage1_c", "temp_stage2_c", "temp_stage3_c",
        "pressure_kpa", "vibration_index", "flow_rate", "efficiency_ratio", "bleed_load",
    ])


def get_all_readings_df(db: Session, building_id: str = DEFAULT_BUILDING_ID) -> pd.DataFrame:
    """Fetches all readings for every asset in the building in a SINGLE database query,
    avoiding the N+1 latency penalty over remote connections."""
    assets = list_assets(db, building_id)
    if not assets:
        return pd.DataFrame()
    asset_ids = [a.asset_id for a in assets]
    rows = (
        db.query(
            AssetReading.asset_id,
            AssetReading.cycle,
            AssetReading.timestamp,
            AssetReading.temp_stage1_c,
            AssetReading.temp_stage2_c,
            AssetReading.temp_stage3_c,
            AssetReading.pressure_kpa,
            AssetReading.vibration_index,
            AssetReading.flow_rate,
            AssetReading.efficiency_ratio,
            AssetReading.bleed_load,
        )
        .filter(AssetReading.asset_id.in_(asset_ids))
        .order_by(AssetReading.asset_id, AssetReading.cycle)
        .all()
    )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=[
        "asset_id", "cycle", "timestamp", "temp_stage1_c", "temp_stage2_c",
        "temp_stage3_c", "pressure_kpa", "vibration_index", "flow_rate",
        "efficiency_ratio", "bleed_load",
    ])


def get_latest_readings_df(db: Session, building_id: str = DEFAULT_BUILDING_ID) -> pd.DataFrame:
    """One row per asset — its most recent reading. Sourced from the single
    bulk query above rather than looping over individual assets."""
    all_df = get_all_readings_df(db, building_id)
    if all_df.empty:
        return pd.DataFrame()
    assets = {a.asset_id: a for a in list_assets(db, building_id)}
    latest = all_df.sort_values("cycle").groupby("asset_id").last().reset_index()
    latest["name"] = latest["asset_id"].map(lambda aid: getattr(assets.get(aid), "name", aid))
    latest["asset_type"] = latest["asset_id"].map(lambda aid: getattr(assets.get(aid), "asset_type", ""))
    latest["location"] = latest["asset_id"].map(lambda aid: getattr(assets.get(aid), "location", ""))
    return latest


# ---- Work orders (the real cross-agent handoff target) ---------------

def open_work_order(
    db: Session,
    asset_id: str,
    reason: str,
    severity: str = "medium",
    source: str = "maintenance_agent",
    building_id: str = DEFAULT_BUILDING_ID,
) -> dict:
    """Creates a real MaintenanceEvent row. Called both by the Maintenance
    Agent's own rule/ML engine AND by the Energy Agent's
    flag_for_maintenance_review tool — see agent_tools.py. `source` records
    which agent actually triggered it, so the handoff is auditable."""
    event = MaintenanceEvent(
        building_id=building_id,
        asset_id=asset_id,
        source=source,
        reason=reason,
        severity=severity,
        status="open",
        created_at=datetime.now(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {
        "id": event.id,
        "asset_id": event.asset_id,
        "source": event.source,
        "reason": event.reason,
        "severity": event.severity,
        "status": event.status,
        "created_at": event.created_at,
    }


def list_work_orders(db: Session, building_id: str = DEFAULT_BUILDING_ID, status: str | None = None) -> list[dict]:
    q = db.query(MaintenanceEvent).filter(MaintenanceEvent.building_id == building_id)
    if status:
        q = q.filter(MaintenanceEvent.status == status)
    events = q.order_by(MaintenanceEvent.created_at.desc()).all()
    return [{
        "id": e.id, "asset_id": e.asset_id, "source": e.source, "reason": e.reason,
        "severity": e.severity, "status": e.status, "created_at": e.created_at,
    } for e in events]


def pick_hvac_asset_for_energy_flag(db: Session, building_id: str = DEFAULT_BUILDING_ID) -> str | None:
    """Used by the Energy Agent's handoff: energy anomalies are most
    plausibly HVAC-related, so route the work order to an actual HVAC-type
    asset in the building if one exists, rather than a made-up placeholder."""
    asset = (
        db.query(Asset)
        .filter(Asset.building_id == building_id, Asset.asset_type.in_(["HVAC Chiller", "Air Handling Unit"]))
        .order_by(Asset.asset_id)
        .first()
    )
    if asset:
        return asset.asset_id
    fallback = db.query(Asset).filter(Asset.building_id == building_id).order_by(Asset.asset_id).first()
    return fallback.asset_id if fallback else None
