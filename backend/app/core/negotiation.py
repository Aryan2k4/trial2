"""
Multi-agent negotiation.

Two domain agents can genuinely disagree over the same real resource:
the Cost Agent wants to hold or cut spend in the "Repairs & Maintenance"
category, while the Maintenance Agent needs that same budget line to pay
for repairing an asset it has independently flagged as Critical/Warning.
Showing both opinions side by side ("Cost says cut, Maintenance says
spend") is not resolution — this module runs an actual negotiation: each
agent states its position from real data, then a neutral mediator is
given both positions verbatim and produces one concrete decision.

This is deliberately NOT triggered on every investigation — see
detect_conflict(): if the real numbers don't actually clash (category is
on-track, or no asset is Critical/Warning), there is nothing to
negotiate and negotiate() says so rather than manufacturing a disagreement.
"""
from sqlalchemy.orm import Session

from app.services import maintenance_service, cost_service
from app.utils.maintenance_analytics import score_fleet
from app.utils.cost_analytics import budget_compliance
from app.services.ai_providers.factory import get_ai_provider
from app.services import agent_memory_service

NEGOTIATION_CATEGORY = "Repairs & Maintenance"

COST_POSITION_SYSTEM_PROMPT = (
    "You are the Cost Agent of a facility operations AI platform. You have been "
    "shown this building's real budget-compliance data for one spend category. "
    "Argue, in under 120 words, for controlling or reducing spend in this "
    "category this month. Reference the actual numbers given — do not invent "
    "data. You are aware a Maintenance Agent may disagree with you over specific "
    "at-risk equipment that draws on this same category; acknowledge that "
    "tension exists but hold your position for now — a mediator will reconcile "
    "the two of you afterward."
)

MAINTENANCE_POSITION_SYSTEM_PROMPT = (
    "You are the Maintenance Agent of a facility operations AI platform. You "
    "have been shown real data on specific assets in Critical or Warning health "
    "status. Argue, in under 120 words, for funding the repair these assets "
    "need. Reference the actual numbers given (health score, predicted "
    "remaining useful life) — do not invent data. You are aware a Cost Agent "
    "wants to hold or cut spend in the category that would pay for this; "
    "acknowledge that tension exists but hold your position for now — a "
    "mediator will reconcile the two of you afterward."
)

MEDIATOR_SYSTEM_PROMPT = (
    "You are the neutral Facility Intelligence mediator in a facility operations "
    "AI platform. Two domain agents disagree: the Cost Agent wants to control "
    "spend in a category; the Maintenance Agent wants that same category's "
    "budget to fund urgent repairs. You are given both agents' stated positions "
    "verbatim, plus the underlying real numbers. Produce a single resolution in "
    "under 150 words: state which specific asset(s) should still get funded "
    "despite the cost pressure, what (if anything) should be deferred or cut "
    "elsewhere to make room, and a one-line rationale. Be concrete and reference "
    "numbers already given — do not invent new ones. This must be an actual "
    "operational decision, not a restatement of the disagreement."
)


def _get_at_risk_assets(db: Session, building_id: str, max_health_score: float = 40.0, limit: int = 5) -> list[dict]:
    assets = maintenance_service.list_assets(db, building_id)
    metas, readings_list = [], []
    for a in assets:
        readings = maintenance_service.get_readings_df(db, a.asset_id)
        if readings.empty:
            continue
        metas.append({"asset_id": a.asset_id, "name": a.name, "asset_type": a.asset_type, "location": a.location})
        readings_list.append(readings)
    scored = score_fleet(metas, readings_list)
    at_risk = [a for a in scored if a["health_score"] <= max_health_score and a["status"] in ("Critical", "Warning")]
    at_risk.sort(key=lambda a: a["health_score"])
    return at_risk[:limit]


def _get_category_compliance(db: Session, building_id: str, category: str) -> dict | None:
    records = cost_service.get_records_df(db, building_id)
    budgets = [
        {"category": b.category, "monthly_budget_inr": b.monthly_budget_inr, "basis": b.basis}
        for b in cost_service.list_budgets(db, building_id)
    ]
    for c in budget_compliance(records, budgets):
        if c["category"] == category:
            return c
    return None


def detect_conflict(db: Session, building_id: str) -> dict | None:
    """Returns a structured conflict if (and only if) the real, current
    data shows one: NEGOTIATION_CATEGORY at "over" or "at_risk" budget
    status AND at least one asset currently Critical/Warning. Returns
    None otherwise — no fabricated disagreement."""
    category_status = _get_category_compliance(db, building_id, NEGOTIATION_CATEGORY)
    if not category_status or category_status["status"] not in ("over", "at_risk"):
        return None
    at_risk_assets = _get_at_risk_assets(db, building_id)
    if not at_risk_assets:
        return None
    return {"category": category_status, "at_risk_assets": at_risk_assets}


def negotiate(db: Session, building_id: str) -> dict:
    """Runs the full 3-round negotiation (Cost position -> Maintenance
    position -> mediator resolution) if a real conflict exists; otherwise
    returns has_conflict: False with a plain reason, and makes no LLM
    calls at all."""
    conflict = detect_conflict(db, building_id)
    if not conflict:
        return {
            "building_id": building_id,
            "has_conflict": False,
            "reason": (
                f"No active conflict: '{NEGOTIATION_CATEGORY}' spend is on-track, or no asset is "
                "currently Critical/Warning — nothing to negotiate right now."
            ),
        }

    category = conflict["category"]
    assets = conflict["at_risk_assets"]

    cost_prompt = (
        f"Category: {category['category']}\nMonth: {category['month']}\n"
        f"Budget: \u20b9{category['budget_inr']}\nSpent so far: \u20b9{category['spent_inr']}\n"
        f"Status: {category['status']} ({category['pct_of_budget']}% of budget)\n"
        f"Budget basis: {category['basis']}"
    )
    maintenance_prompt = "Assets currently at risk:\n" + "\n".join(
        f"- {a['asset_id']} ({a['name']}, {a['asset_type']}): health {a['health_score']}/100, "
        f"status {a['status']}, predicted remaining useful life {a['predicted_rul_cycles']} cycles"
        for a in assets
    )

    provider, provider_name = get_ai_provider()
    # Local import avoids a circular import at module load time
    # (intelligence_engine.py is the module other API routes import from
    # first; negotiation.py is a one-directional consumer of its safety
    # wrapper, not the other way around).
    from app.core.intelligence_engine import _safe_generate

    cost_position, cost_provider, cost_err = _safe_generate(
        provider, provider_name, COST_POSITION_SYSTEM_PROMPT, cost_prompt
    )
    maintenance_position, maint_provider, maint_err = _safe_generate(
        provider, provider_name, MAINTENANCE_POSITION_SYSTEM_PROMPT, maintenance_prompt
    )
    mediator_prompt = (
        f"Cost Agent's position:\n{cost_position}\n\n"
        f"Maintenance Agent's position:\n{maintenance_position}\n\n"
        f"Underlying data:\n{cost_prompt}\n\n{maintenance_prompt}\n\n"
        "Produce your resolution now."
    )
    resolution, mediator_provider, mediator_err = _safe_generate(
        provider, provider_name, MEDIATOR_SYSTEM_PROMPT, mediator_prompt
    )

    result = {
        "building_id": building_id,
        "has_conflict": True,
        "category": category,
        "at_risk_assets": assets,
        "rounds": [
            {"agent": "cost", "position": cost_position, "provider": cost_provider, "provider_error": cost_err},
            {"agent": "maintenance", "position": maintenance_position, "provider": maint_provider, "provider_error": maint_err},
            {"agent": "mediator", "position": resolution, "provider": mediator_provider, "provider_error": mediator_err},
        ],
        "resolution": resolution,
    }

    agent_memory_service.save_memory(
        db, building_id, domain="negotiation:cost-maintenance",
        summary=resolution, tool_call_count=0,
        key_findings=[f"{a['asset_id']}: {a['status']} ({a['health_score']}/100)" for a in assets],
        provider=mediator_provider,
    )
    return result
