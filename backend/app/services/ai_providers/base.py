"""
AI provider abstraction — same pattern as AG-ASE-2026's AIProvider interface.
Lets the Intelligence Engine swap between real LLM providers (Gemini, Groq,
OpenAI) and a MockProvider for tests/dev without an API key, without
touching any calling code.
"""
from abc import ABC, abstractmethod
from typing import Callable, Generator


class AIProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model's text response for a single-turn prompt
        (no tool use). Used for straightforward summarization tasks."""
        raise NotImplementedError

    @abstractmethod
    def run_agentic_task(self, system_prompt: str, task_prompt: str, tools: list[Callable], building_id: str = "BLD-HQ-01") -> dict:
        """
        Run a genuinely agentic task: the model is given a goal and a set
        of callable tools, and DECIDES for itself which tools to call, in
        what order, and when it has enough information to stop — as
        opposed to us hardcoding a fixed pipeline of calls.

        building_id is also stated in task_prompt's own text (e.g.
        "...for building BLD-EAST-02") — real LLM providers extract it
        from there via ordinary tool-calling reasoning and can ignore this
        parameter. It's passed explicitly for providers with no such
        reasoning to fall back on: MockProvider used to hardcode
        "BLD-HQ-01" into every simulated tool call regardless of which
        building was actually being investigated, silently breaking any
        building other than the default one whenever no real LLM API key
        is configured (MockProvider is the default with no key set).

        Returns:
            {
                "final_text": str,              # the model's final synthesis
                "tool_calls": [                  # trace of what the model decided to do
                    {"tool": str, "args": dict, "result": Any}, ...
                ],
            }
        """
        raise NotImplementedError

    def run_agentic_task_stream(
        self, system_prompt: str, task_prompt: str, tools: list[Callable], building_id: str = "BLD-HQ-01"
    ) -> Generator[dict, None, None]:
        """
        Streaming counterpart of run_agentic_task(): yields events as the
        investigation progresses instead of returning only once it's fully
        done, so a UI can show tool calls landing live and the final
        narrative appearing token-by-token rather than after one long wait.

        Event shapes yielded, in order:
            {"type": "tool_call", "tool": str, "args": dict, "result": Any}  (zero or more)
            {"type": "token", "text": str}                                   (one or more)
            {"type": "done", "tool_calls": [...], "final_text": str}         (exactly one, last)

        DEFAULT IMPLEMENTATION (used by any provider that doesn't override
        this, e.g. GeminiProvider/MockProvider): runs the existing
        non-streaming run_agentic_task() to completion, then REPLAYS its
        trace and final text as the same event stream, chunked
        word-by-word. This keeps every provider streaming-compatible
        without forcing each one to reimplement the tool-calling loop, at
        the honest cost that these providers only *appear* incremental
        client-side — the real work already finished before the first
        event is yielded. GroqProvider overrides this with a genuine
        mid-flight stream (see groq_provider.py).
        """
        result = self.run_agentic_task(system_prompt, task_prompt, tools, building_id)
        for call in result["tool_calls"]:
            yield {"type": "tool_call", **call}
        words = (result["final_text"] or "").split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            if chunk:
                yield {"type": "token", "text": chunk}
        yield {"type": "done", "tool_calls": result["tool_calls"], "final_text": result["final_text"]}
