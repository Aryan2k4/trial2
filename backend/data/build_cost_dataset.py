"""
Generates a synthetic placeholder Cost dataset — same honesty note as
build_energy_dataset.py (see that file). The real project used actual
BBMP (Bengaluru) capital-works tender data (see cost_service.py's
module docstring), which is not available in this handout's zip and
isn't something this script attempts to reproduce; this is fabricated
plausible-shaped vendor/spend data purely so the dashboard has real rows
to run against.

Usage:
    cd backend && python data/build_cost_dataset.py
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = DATA_DIR / "processed"
MONTHS = 8

CATEGORIES = [
    "Repairs & Maintenance", "Utilities", "Cleaning Services",
    "Security Services", "Landscaping", "IT & Software",
]
VENDORS = [
    ("VEN-001", "Apex Facility Services", "Repairs & Maintenance"),
    ("VEN-002", "BrightPower Utilities", "Utilities"),
    ("VEN-003", "CleanSweep Co", "Cleaning Services"),
    ("VEN-004", "Sentinel Security Group", "Security Services"),
    ("VEN-005", "GreenScape Landscaping", "Landscaping"),
    ("VEN-006", "NimbusTech Solutions", "IT & Software"),
    ("VEN-007", "Reliable Repairs Ltd", "Repairs & Maintenance"),
]
MONTHLY_BUDGET = {
    "Repairs & Maintenance": 45000, "Utilities": 120000, "Cleaning Services": 30000,
    "Security Services": 40000, "Landscaping": 15000, "IT & Software": 60000,
}


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.RandomState(21)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30 * MONTHS)

    records = []
    rec_id = 1
    d = start
    while d < now:
        n_today = rng.poisson(1.1)
        for _ in range(n_today):
            vendor_id, vendor_name, category = VENDORS[rng.randint(len(VENDORS))]
            base = MONTHLY_BUDGET[category] / 22  # ~22 spend-days/month
            amount = max(200.0, rng.lognormal(mean=np.log(base), sigma=0.6))
            # Occasionally push Repairs & Maintenance over budget so the
            # negotiation feature (Cost vs Maintenance conflict) has real
            # data to detect rather than always reporting "no conflict".
            if category == "Repairs & Maintenance" and rng.random() < 0.25:
                amount *= rng.uniform(1.8, 2.6)
            records.append({
                "record_id": f"REC-{rec_id:05d}", "vendor_id": vendor_id, "vendor_name": vendor_name,
                "category": category, "date": d.date().isoformat(), "amount_inr": round(amount, 2),
                "description": f"{category} — {vendor_name}", "po_number": f"PO-{rec_id:05d}",
            })
            rec_id += 1
        d += timedelta(days=1)

    records_df = pd.DataFrame(records)
    records_df.to_csv(PROCESSED_DIR / "cost_records.csv", index=False)

    vendor_rows = []
    for vendor_id, vendor_name, category in VENDORS:
        v_records = records_df[records_df["vendor_id"] == vendor_id]
        vendor_rows.append({
            "vendor_id": vendor_id, "vendor_name": vendor_name, "primary_category": category,
            "order_count": len(v_records), "total_spend_inr": round(v_records["amount_inr"].sum(), 2),
        })
    pd.DataFrame(vendor_rows).to_csv(PROCESSED_DIR / "cost_vendors.csv", index=False)

    budgets_df = pd.DataFrame([
        {"category": c, "monthly_budget_inr": b, "basis": "estimated facility-operations baseline"}
        for c, b in MONTHLY_BUDGET.items()
    ])
    budgets_df.to_csv(PROCESSED_DIR / "cost_budgets.csv", index=False)

    print(f"Wrote {len(records_df)} records, {len(vendor_rows)} vendors, {len(budgets_df)} budgets to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
