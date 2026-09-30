"""
Persistent cross-investigation memory for every domain agent.

Without this, each /investigate call is a fresh, stateless LLM run: the
same stale anomaly gets "discovered" every time nothing else changed.
With it, every investigate_*() call in intelligence_engine.py first
fetches the domain's recent memory for this building and folds a short
"what you found last time" recap into the task prompt, then writes its
own new summary back before returning — so the NEXT investigation can
build on this one (e.g. "you flagged AST-014 as Critical 2 investigations
ago and opened a work order; is it still Critical, or did the repair
help?").
"""
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.agent_memory_models import AgentMemory

MAX_FINDINGS_PER_ENTRY = 5
DEFAULT_HISTORY_LIMIT = 3


def save_memory(
    db: Session,
    building_id: str,
    domain: str,
    summary: str,
    tool_call_count: int = 0,
    key_findings: list[str] | None = None,
    provider: str | None = None,
) -> AgentMemory:
    entry = AgentMemory(
        building_id=building_id,
        domain=domain,
        created_at=datetime.now(timezone.utc),
        summary=summary[:2000],
        key_findings=json.dumps((key_findings or [])[:MAX_FINDINGS_PER_ENTRY]),
        tool_call_count=tool_call_count,
        provider=provider,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_recent_memories(
    db: Session, building_id: str, domain: str, limit: int = DEFAULT_HISTORY_LIMIT
) -> list[dict]:
    rows = (
        db.query(AgentMemory)
        .filter(AgentMemory.building_id == building_id, AgentMemory.domain == domain)
        .order_by(AgentMemory.created_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for r in rows:
        try:
            findings = json.loads(r.key_findings) if r.key_findings else []
        except (json.JSONDecodeError, TypeError):
            findings = []
        out.append({
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "summary": r.summary,
            "key_findings": findings,
            "tool_call_count": r.tool_call_count,
            "provider": r.provider,
        })
    return out


def format_memory_context(memories: list[dict]) -> str:
    """Turns stored memory rows into a short block to prepend to a task
    prompt. Returns "" (no block at all) when there's no history yet, so
    the very first investigation for a building reads identically to
    before this feature existed."""
    if not memories:
        return ""
    lines = ["Context from your past investigations of this building (most recent first):"]
    for m in memories:
        lines.append(f"- [{m['created_at'][:16]}] {m['summary'][:280]}")
    lines.append(
        "Use this only as background — re-verify current numbers with your tools rather than "
        "assuming nothing has changed, and call out explicitly if something has improved, "
        "worsened, or stayed the same since then."
    )
    return "\n".join(lines) + "\n\n"


def extract_key_findings(tool_calls: list[dict], final_text: str) -> list[str]:
    """Pulls a handful of short, structured bullet points out of a raw
    tool-call trace for storage, so future context recaps stay compact
    instead of dumping full tool JSON back into a future prompt. Prefers
    calls that represent a real handoff/action (work order, alert,
    flag_for_*) since those are the ones worth remembering; falls back to
    just noting which read-only tools were checked."""
    action_tools = {
        "create_work_order", "create_cost_alert", "create_security_alert",
        "flag_for_maintenance_review", "flag_restricted_zone_for_security_review",
    }
    findings = []
    for call in tool_calls:
        name = call.get("tool", "")
        if name in action_tools:
            args = call.get("args", {})
            descriptor = args.get("reason") or args.get("description") or str(args)
            findings.append(f"{name}: {descriptor}"[:200])
    if not findings and tool_calls:
        checked = ", ".join(sorted({c.get("tool", "") for c in tool_calls}))
        findings.append(f"Checked: {checked}"[:200])
    return findings[:MAX_FINDINGS_PER_ENTRY]
