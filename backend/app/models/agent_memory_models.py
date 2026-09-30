from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.core.database import Base


class AgentMemory(Base):
    """Persistent record of one agent investigation (or negotiation), kept
    so a FUTURE investigation for the same building+domain can be given
    real prior context ("last time you flagged X, has it changed?")
    instead of starting from a blank slate every run. This is what makes
    repeated investigations agentic memory rather than a stateless API
    call that happens to use an LLM.

    domain is one of: energy | maintenance | occupancy | security | cost |
    facility | negotiation:<domain_a>-<domain_b>
    """
    __tablename__ = "agent_memories"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(String, index=True, nullable=False)
    domain = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, index=True, nullable=False)
    summary = Column(Text, nullable=False)
    key_findings = Column(Text, nullable=True)  # JSON-encoded list[str], kept short & structured
    tool_call_count = Column(Integer, nullable=False, default=0)
    provider = Column(String, nullable=True)
