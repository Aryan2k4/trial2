"""
Intelligence Engine — the LLM reasoning layer that sits above individual
agents (Energy, and later Maintenance/Occupancy/Security/Cost).

Two distinct capabilities live here:

1. summarize_energy_analysis() — a single-shot LLM call that takes the
   Energy Agent's already-computed rule-based output and writes a plain-
   English briefing. Useful, but NOT agentic: we decided what to compute
   and just asked the model to narrate it.

2. investigate_energy() — a genuinely agentic run. The model is given a
   goal and a set of real tools (app/core/agent_tools.py) and DECIDES for
   itself which analyses to run, in what order, and whether the evidence
   warrants flagging the finding to another agent. This is the actual
   "agentic AI" component of the platform, as distinct from a fixed
   pipeline or a single summarization call.
"""
import logging
from app.services.ai_providers.factory import get_ai_provider
from app.services.ai_providers.mock_provider import MockProvider
from app.core.agent_tools import ALL_TOOLS
from app.core.maintenance_tools import ALL_TOOLS as MAINTENANCE_TOOLS
from app.core.occupancy_tools import ALL_TOOLS as OCCUPANCY_TOOLS
from app.core.security_tools import ALL_TOOLS as SECURITY_TOOLS
from app.core.cost_tools import ALL_TOOLS as COST_TOOLS
from app.services import agent_memory_service

# Every domain's tools combined, deduplicated by function identity — this
# is what makes the Facility Intelligence Agent below "cross-domain": it is
# the exact same real tool functions each single-domain agent uses (so a
# handoff it makes is a genuine action, not a simulated one), just handed
# to one model at once instead of five separate ones.
CROSS_DOMAIN_TOOLS = list(dict.fromkeys(
    ALL_TOOLS + MAINTENANCE_TOOLS + OCCUPANCY_TOOLS + SECURITY_TOOLS + COST_TOOLS
))

logger = logging.getLogger(__name__)


def _safe_generate(provider, provider_name: str, system_prompt: str, user_prompt: str) -> tuple[str, str, str | None]:
    """Runs provider.generate() but never lets a runtime API failure (bad
    key, rate limit, network blip) crash the request — falls back to
    MockProvider's deterministic output, the same way factory.py already
    falls back when the key is missing entirely.

    Returns (text, provider_name, error_detail) — error_detail is None on
    success. The raw exception is DELIBERATELY NOT appended to the
    returned text anymore (it used to be, as a "[Note: ... API call
    failed ...]" tacked onto the end of the briefing/summary) — a raw
    stack-trace-shaped string in the middle of what's supposed to read as
    a plain-English briefing looked unpolished and confusing to anyone
    who didn't already know why the fallback happened. The error is still
    fully preserved, just returned as its own field so the frontend can
    show it in a small, clearly-labeled badge/tooltip instead of inline
    in the prose."""
    try:
        return provider.generate(system_prompt, user_prompt), provider_name, None
    except Exception as e:
        logger.warning(f"{provider_name} generate() call failed at runtime ({e}); falling back to MockProvider.")
        fallback = MockProvider().generate(system_prompt, user_prompt)
        return fallback, f"{provider_name} (unavailable)", str(e)


def _safe_agentic_task(provider, provider_name: str, system_prompt: str, task_prompt: str, tools: list, building_id: str = "BLD-HQ-01") -> tuple[dict, str, str | None]:
    """Same runtime-failure safety net as _safe_generate(), for the
    agentic tool-calling path — see its docstring for why the error is a
    separate return value now instead of appended text."""
    try:
        return provider.run_agentic_task(system_prompt, task_prompt, tools, building_id), provider_name, None
    except Exception as e:
        logger.warning(f"{provider_name} run_agentic_task() call failed at runtime ({e}); falling back to MockProvider.")
        result = MockProvider().run_agentic_task(system_prompt, task_prompt, tools, building_id)
        return result, f"{provider_name} (unavailable)", str(e)

SUMMARY_SYSTEM_PROMPT = (
    "You are the Intelligence Engine of a facility operations AI platform. "
    "You receive structured analytics and rule-based recommendations from a "
    "domain agent (e.g. the Energy Agent) and must synthesize them into a "
    "short, prioritized, plain-English briefing for a facility manager. "
    "Be concrete and reference the actual numbers given. Do not invent data "
    "that wasn't provided. Keep it under 200 words."
)

INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Energy Agent of a facility operations AI platform, "
    "investigating a building's energy efficiency. You have tools to pull "
    "consumption data, submeter breakdowns, anomalies, temperature and "
    "occupancy correlations, and an ML-based forecast (available at 1h, 6h, "
    "or 24h horizons — each backed by a separately trained model with "
    "different accuracy; the forecast tool's response includes a confidence "
    "field you should factor into how much weight you give the prediction, "
    "especially at 24h where accuracy is only marginal). You do NOT have to "
    "call every tool — decide which ones are actually relevant based on "
    "what you learn as you go, and only check longer forecast horizons if "
    "the near-term signal actually warrants it. If you find evidence "
    "suggesting an equipment fault (e.g. multiple high-severity anomalies) "
    "rather than a scheduling issue, use the flag_for_maintenance_review "
    "tool to hand it off. When you have enough information, write a short "
    "(under 200 words) plain-English investigation summary explaining what "
    "you checked, why, and what you found. Reference actual numbers from "
    "the tool results."
)


MAINTENANCE_INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Maintenance Agent of a facility operations AI platform, "
    "investigating the health of a building's equipment fleet. You have "
    "tools to pull the fleet-wide health summary, drill into a specific "
    "asset's ML-predicted health (remaining useful life, health score, "
    "predicted maintenance date, and the model's own confidence), list the "
    "assets currently most at risk, and open a real maintenance work order. "
    "You do NOT have to call every tool — start broad (fleet summary), "
    "narrow to at-risk assets only if the fleet summary suggests a problem, "
    "and only open work orders for assets where the evidence is clear "
    "(Critical status, or Warning with limited remaining life) — do not "
    "open work orders speculatively for every asset you inspect. When you "
    "have enough information, write a short (under 200 words) plain-"
    "English investigation summary explaining what you checked, why, and "
    "what you found, referencing actual numbers from the tool results."
)


OCCUPANCY_INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Occupancy Agent of a facility operations AI platform, "
    "investigating space utilization across a building. You have tools to "
    "pull the building-wide occupancy summary, drill into a specific "
    "zone's current status, list zones currently overcrowded, check the "
    "status of restricted zones specifically (e.g. server rooms — worth "
    "checking even when nowhere near the general overcrowding threshold, "
    "since ANY occupancy there is unusual), and — important — flag a "
    "restricted zone for Security review if it shows occupancy, since "
    "headcount data alone can't confirm who is present or whether their "
    "access was authorized. Only use the security handoff tool for "
    "zone_type='restricted' zones with actual current occupancy, not for "
    "ordinary workspace/meeting-room overcrowding. When you have enough "
    "information, write a short (under 200 words) plain-English "
    "investigation summary explaining what you checked, why, and what you "
    "found, referencing actual numbers from the tool results."
)


SECURITY_INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Security Agent of a facility operations AI platform, "
    "investigating access-control activity across a building. You have "
    "tools to pull the building-wide security summary, list recent events "
    "the anomaly detector flagged (with an anomaly score — higher means "
    "more statistically unusual), check a specific access point's "
    "configured risk level (low/medium/high), and open a real security "
    "alert. The anomaly detector is honest but imperfect (see its own "
    "precision/recall in the tool results if surfaced) — weigh anomaly "
    "score together with the access point's risk level, and only open "
    "alerts where the evidence is clear (a high anomaly score at a "
    "medium/high-risk access point, or a repeated-denial pattern) rather "
    "than for every flagged event. When you have enough information, "
    "write a short (under 200 words) plain-English investigation summary "
    "explaining what you checked, why, and what you found, referencing "
    "actual numbers from the tool results."
)


COST_INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Cost Optimization Agent of a facility operations AI "
    "platform, investigating facility spend. You have tools to pull the "
    "overall spend summary, check budget compliance by category "
    "(budgets are assumption-based, not a real published figure — the "
    "tool result says so), list invoices the anomaly detector flagged as "
    "statistically unusual (no labeled ground truth exists for this real "
    "invoice data, so treat a flag as a lead, not a confirmed error), "
    "check the ML spend-trend forecast (only ~27 weeks of real training "
    "data — weigh its reported confidence), check vendor concentration "
    "risk, and open a real cost alert. Only open alerts where the "
    "evidence is clear (a category clearly over budget, or a "
    "high-confidence flagged invoice at a concentrated vendor) — not for "
    "every data point you check. When you have enough information, write "
    "a short (under 200 words) plain-English investigation summary "
    "explaining what you checked, why, and what you found, referencing "
    "actual numbers from the tool results."
)


CROSS_DOMAIN_INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Facility Intelligence Agent of a facility operations AI "
    "platform — unlike the five domain agents (Energy, Maintenance, "
    "Occupancy, Security, Cost), which each investigate one thing, you "
    "have ALL of their tools at once and your job is specifically to look "
    "for CROSS-DOMAIN correlations a single-domain agent would never see: "
    "e.g. whether energy anomalies line up with equipment nearing failure "
    "(Energy + Maintenance), whether occupancy in a restricted zone "
    "coincides with a flagged security event (Occupancy + Security), "
    "whether a maintenance work order's asset/location matches an area "
    "with an energy or cost anomaly (Maintenance + Energy/Cost), or "
    "whether a category over budget is explained by a flagged invoice "
    "concentrated at one vendor (Cost). Start by pulling the summary tool "
    "from at least three different domains to get a baseline picture "
    "before you decide which specific correlation is worth chasing — do "
    "not just repeat one domain's own investigation. Only call the more "
    "expensive/specific tools (asset drill-downs, zone drill-downs, "
    "flagged-event lists) once a summary tool actually suggests there is "
    "something there to explain. You may use the handoff tools "
    "(flag_for_maintenance_review, flag_restricted_zone_for_security_"
    "review, create_work_order, create_security_alert, create_cost_alert) "
    "if the cross-domain evidence genuinely warrants it, but do not "
    "duplicate an action a single-domain agent would already take on "
    "unremarkable single-domain evidence — the bar here is specifically "
    "'this only makes sense when you look at two domains together'. When "
    "you have enough information, write a short (under 220 words) plain-"
    "English investigation summary explicitly naming which domains you "
    "connected and how, referencing actual numbers from the tool results. "
    "If you genuinely found no cross-domain correlation worth reporting, "
    "say so plainly rather than manufacturing a connection."
)



def summarize_energy_analysis(analysis: dict, recommendations: list[dict]) -> tuple[str, str, str | None]:
    provider, provider_name = get_ai_provider()

    consumption = analysis.get("consumption", {})
    breakdown = analysis.get("breakdown", {})
    trend = analysis.get("trend_pct_vs_prev_period")
    occupancy = analysis.get("occupancy", {})

    user_prompt = f"""
Energy analysis for this period:
- Total consumption: {consumption.get('total_kwh')} kWh
- Peak load: {consumption.get('peak_kwh')} kWh
- Trend vs previous period: {trend}%
- Load breakdown: HVAC {breakdown.get('hvac_pct')}%, Lighting {breakdown.get('lighting_pct')}%, \
Plug load {breakdown.get('plug_load_pct')}%, Other {breakdown.get('other_pct')}%
- Unoccupied-period load: {occupancy.get('unoccupied_load_pct_of_occupied', 'n/a')}% of occupied-period average

Top recommendations (already ranked by severity):
{chr(10).join(f"- [{r['severity'].upper()}] {r['title']}: {r['description']}" for r in recommendations[:5])}

Write a short briefing synthesizing the above for a facility manager.
"""
    return _safe_generate(provider, provider_name, SUMMARY_SYSTEM_PROMPT, user_prompt)


def _run_investigation(domain: str, building_id: str, db, system_prompt: str, task_prompt: str, tools: list) -> dict:
    """
    Shared investigation runner used by every investigate_*() function
    below. Two responsibilities beyond the plain agentic tool-calling
    run:

    1. MEMORY IN: if a db session is given, fetches this building+domain's
       recent past investigations and prepends them to the task prompt,
       so the agent has real continuity across runs instead of
       rediscovering the same finding from a blank slate every time.
    2. MEMORY OUT: after the run, persists a compact summary + key
       findings back to the same store, so the NEXT investigation
       (whenever it happens) gets this one as context.

    db is optional (default None from callers that don't have a session,
    e.g. ad-hoc scripts) — memory is simply skipped in that case, and the
    function behaves exactly as it did before this feature existed.
    """
    provider, provider_name = get_ai_provider()

    memory_context = ""
    if db is not None:
        past = agent_memory_service.get_recent_memories(db, building_id, domain)
        memory_context = agent_memory_service.format_memory_context(past)

    full_task_prompt = memory_context + task_prompt
    result, provider_name, provider_error = _safe_agentic_task(provider, provider_name, system_prompt, full_task_prompt, tools, building_id)

    if db is not None:
        findings = agent_memory_service.extract_key_findings(result["tool_calls"], result["final_text"])
        agent_memory_service.save_memory(
            db, building_id, domain, result["final_text"],
            tool_call_count=len(result["tool_calls"]), key_findings=findings, provider=provider_name,
        )

    return {
        "building_id": building_id,
        "final_summary": result["final_text"],
        "tool_calls": result["tool_calls"],
        "tool_call_count": len(result["tool_calls"]),
        "provider": provider_name,
        "provider_error": provider_error,
        "had_memory_context": bool(memory_context),
    }


def _run_investigation_stream(domain: str, building_id: str, db, system_prompt: str, task_prompt: str, tools: list):
    """
    Streaming counterpart of _run_investigation(): yields the same
    "tool_call"/"token"/"done" events as AIProvider.run_agentic_task_stream(),
    but also handles the memory read/write around the stream (context in
    before the first event, save-back after the final "done" event) so
    every domain's stream endpoint gets memory continuity for free too.
    Falls back to MockProvider's (also-streaming, via the base class
    default) output on any runtime provider failure, same safety net as
    _safe_agentic_task, just applied to a generator instead of a
    return value.
    """
    provider, provider_name = get_ai_provider()

    memory_context = ""
    if db is not None:
        past = agent_memory_service.get_recent_memories(db, building_id, domain)
        memory_context = agent_memory_service.format_memory_context(past)
    full_task_prompt = memory_context + task_prompt

    yield {"type": "meta", "provider": provider_name, "had_memory_context": bool(memory_context)}

    try:
        stream = provider.run_agentic_task_stream(system_prompt, full_task_prompt, tools, building_id)
        final_tool_calls, final_text = [], ""
        for event in stream:
            if event["type"] == "done":
                final_tool_calls, final_text = event["tool_calls"], event["final_text"]
            yield event
    except Exception as e:
        logger.warning(f"{provider_name} run_agentic_task_stream() call failed at runtime ({e}); falling back to MockProvider.")
        yield {"type": "meta", "provider": f"{provider_name} (unavailable)", "provider_error": str(e)}
        final_tool_calls, final_text = [], ""
        for event in MockProvider().run_agentic_task_stream(system_prompt, full_task_prompt, tools, building_id):
            if event["type"] == "done":
                final_tool_calls, final_text = event["tool_calls"], event["final_text"]
            yield event
        provider_name = f"{provider_name} (unavailable)"

    if db is not None:
        findings = agent_memory_service.extract_key_findings(final_tool_calls, final_text)
        agent_memory_service.save_memory(
            db, building_id, domain, final_text,
            tool_call_count=len(final_tool_calls), key_findings=findings, provider=provider_name,
        )


def investigate_energy(building_id: str = "BLD-HQ-01", db=None) -> dict:
    """
    Runs the agentic investigation: the model (or, with MockProvider, a
    simulated stand-in) decides which of the available tools to call and
    in what order to reach a conclusion about this building's energy
    efficiency. Returns the final narrative plus the full decision trace.
    """
    task_prompt = f"Investigate energy efficiency for building {building_id}."
    return _run_investigation("energy", building_id, db, INVESTIGATION_SYSTEM_PROMPT, task_prompt, ALL_TOOLS)


def investigate_energy_stream(building_id: str = "BLD-HQ-01", db=None):
    task_prompt = f"Investigate energy efficiency for building {building_id}."
    yield from _run_investigation_stream("energy", building_id, db, INVESTIGATION_SYSTEM_PROMPT, task_prompt, ALL_TOOLS)


def investigate_maintenance(building_id: str = "BLD-HQ-01", db=None) -> dict:
    """
    Same genuinely-agentic pattern as investigate_energy(), pointed at the
    Maintenance Agent's tools instead. The model (or MockProvider's
    conditional simulation) decides which assets are worth a closer look
    and whether the evidence warrants opening a real work order.
    """
    task_prompt = f"Investigate equipment health for building {building_id}."
    return _run_investigation("maintenance", building_id, db, MAINTENANCE_INVESTIGATION_SYSTEM_PROMPT, task_prompt, MAINTENANCE_TOOLS)


def investigate_maintenance_stream(building_id: str = "BLD-HQ-01", db=None):
    task_prompt = f"Investigate equipment health for building {building_id}."
    yield from _run_investigation_stream("maintenance", building_id, db, MAINTENANCE_INVESTIGATION_SYSTEM_PROMPT, task_prompt, MAINTENANCE_TOOLS)


def investigate_occupancy(building_id: str = "BLD-HQ-01", db=None) -> dict:
    """
    Same genuinely-agentic pattern, pointed at the Occupancy Agent's tools.
    The model decides which zones are worth a closer look and whether a
    restricted zone's occupancy warrants a real handoff to Security.
    """
    task_prompt = f"Investigate space utilization and occupancy for building {building_id}."
    return _run_investigation("occupancy", building_id, db, OCCUPANCY_INVESTIGATION_SYSTEM_PROMPT, task_prompt, OCCUPANCY_TOOLS)


def investigate_occupancy_stream(building_id: str = "BLD-HQ-01", db=None):
    task_prompt = f"Investigate space utilization and occupancy for building {building_id}."
    yield from _run_investigation_stream("occupancy", building_id, db, OCCUPANCY_INVESTIGATION_SYSTEM_PROMPT, task_prompt, OCCUPANCY_TOOLS)


def investigate_security(building_id: str = "BLD-HQ-01", db=None) -> dict:
    """
    Same genuinely-agentic pattern, pointed at the Security Agent's tools.
    The model decides which flagged events warrant a real alert, weighing
    anomaly score against access-point risk level rather than alerting on
    every flag.
    """
    task_prompt = f"Investigate access-control activity for building {building_id}."
    return _run_investigation("security", building_id, db, SECURITY_INVESTIGATION_SYSTEM_PROMPT, task_prompt, SECURITY_TOOLS)


def investigate_security_stream(building_id: str = "BLD-HQ-01", db=None):
    task_prompt = f"Investigate access-control activity for building {building_id}."
    yield from _run_investigation_stream("security", building_id, db, SECURITY_INVESTIGATION_SYSTEM_PROMPT, task_prompt, SECURITY_TOOLS)


def investigate_cost(building_id: str = "BLD-HQ-01", db=None) -> dict:
    """
    Same genuinely-agentic pattern, pointed at the Cost Agent's tools.
    The model decides which budget risks, flagged invoices, or vendor-
    concentration signals are worth a real cost alert.
    """
    task_prompt = f"Investigate facility spend and cost-optimization opportunities for building {building_id}."
    return _run_investigation("cost", building_id, db, COST_INVESTIGATION_SYSTEM_PROMPT, task_prompt, COST_TOOLS)


def investigate_cost_stream(building_id: str = "BLD-HQ-01", db=None):
    task_prompt = f"Investigate facility spend and cost-optimization opportunities for building {building_id}."
    yield from _run_investigation_stream("cost", building_id, db, COST_INVESTIGATION_SYSTEM_PROMPT, task_prompt, COST_TOOLS)


def investigate_facility(building_id: str = "BLD-HQ-01", db=None) -> dict:
    """
    The Facility Intelligence Agent (Milestone 4's "cross-combined" agent):
    unlike investigate_energy()/investigate_maintenance()/etc., which each
    reason over ONE domain's tools, this gives the model every domain's
    tools at once specifically to look for correlations a single-domain
    agent structurally cannot see (e.g. an energy anomaly and a
    maintenance risk signal at the same asset/time; occupancy in a
    restricted zone coinciding with a flagged security event). Returns the
    same shape as the single-domain investigate_*() functions plus
    `domains_available` so the caller can show which tools were in scope.
    """
    task_prompt = (
        f"Investigate building {building_id} for correlations across the Energy, "
        "Maintenance, Occupancy, Security, and Cost domains that a single-domain "
        "agent would not surface on its own."
    )
    result = _run_investigation("facility", building_id, db, CROSS_DOMAIN_INVESTIGATION_SYSTEM_PROMPT, task_prompt, CROSS_DOMAIN_TOOLS)
    result["domains_available"] = ["energy", "maintenance", "occupancy", "security", "cost"]
    return result


def investigate_facility_stream(building_id: str = "BLD-HQ-01", db=None):
    task_prompt = (
        f"Investigate building {building_id} for correlations across the Energy, "
        "Maintenance, Occupancy, Security, and Cost domains that a single-domain "
        "agent would not surface on its own."
    )
    yield from _run_investigation_stream("facility", building_id, db, CROSS_DOMAIN_INVESTIGATION_SYSTEM_PROMPT, task_prompt, CROSS_DOMAIN_TOOLS)
