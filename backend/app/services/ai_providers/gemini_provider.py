"""
Real Gemini-backed provider. Requires GEMINI_API_KEY in the environment.
Uses the google-genai SDK — same choice as AG-ASE-2026 for consistency.

MODEL DEPRECATION NOTE (fixed AGAIN, third time — see git history): every
hardcoded default here has gone dead within weeks of being set (2.0-flash →
2.5-flash → 2.5-flash-lite, each confirmed-dead in turn). Google's Sept
2026 model page (ai.google.dev/gemini-api/docs/models) lists gemini-3.7-flash
as newest/"most capable", gemini-3.6-flash as stable, gemini-3.5-flash-lite
as the current cheap/fast stable option — all three GA per Google's own
docs at time of writing. To stop this recurring bug from needing a code
change every time: GEMINI_MODEL in .env, if set, is tried FIRST, ahead of
the hardcoded chain — see GEMINI_MODEL commented example in backend/.env.
IF THIS BREAKS AGAIN: set GEMINI_MODEL in .env to whatever Google's
current docs recommend — don't wait for a code fix.
"""
import os
import logging
from typing import Callable
from app.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

MODEL_FALLBACK_CHAIN = ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]

# Tried in order; only advances to the next if the current one raises —
# survives a model being retired without falling all the way back to mock.
MODEL_FALLBACK_CHAIN = ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-2.5-flash-lite"]


class GeminiProvider(AIProvider):
    def __init__(self, model: str | None = None):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Add it to backend/.env to use GeminiProvider, "
                "or use MockProvider for local dev without a key."
            )
        # GEMINI_MODEL in .env, if set, is tried FIRST — lets a model swap
        # (the recurring failure mode this file keeps hitting) be fixed by
        # editing .env instead of this source file and redeploying.
        model = model or os.getenv("GEMINI_MODEL") or MODEL_FALLBACK_CHAIN[0]
        from google import genai
        # http_options timeout — WITHOUT this, a stalled/slow network path to
        # Gemini (common on restricted egress / free-tier hosting like
        # Render) hangs until the underlying TCP connection times out, which
        # can take minutes — and since this call sits inside a
        # Promise.all() on the frontend (see EnergyDashboardPage.jsx's
        # briefing fetch), that hang blocks the ENTIRE dashboard from
        # rendering, not just the AI briefing card. 12s is generous for a
        # single short generate_content call but fails fast enough that the
        # _safe_generate()/_safe_agentic_task() mock fallback actually
        # kicks in within a human-tolerable wait.
        from google.genai import types
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=12_000))
        self.model = model
        self._models_to_try = [model] + [m for m in MODEL_FALLBACK_CHAIN if m != model]

    def _call_with_fallback(self, fn):
        last_error = None
        attempted = []
        for model in self._models_to_try:
            try:
                result = fn(model)
                if model != self.model:
                    logger.warning(f"Gemini model '{self.model}' failed; '{model}' succeeded instead. "
                                    f"Consider updating the default in gemini_provider.py.")
                return result
            except Exception as e:
                last_error = e
                attempted.append(f"{model}: {e}")
                continue
        # Log EVERY model's failure, not just the last one — a fresh error
        # message showing only the last-tried model's 404 (e.g.
        # gemini-2.5-flash-lite) makes it easy to assume just that one
        # model needs updating, when actually every model ahead of it in
        # the chain failed too. This exact ambiguity delayed diagnosing a
        # real production issue once already.
        logger.error("All Gemini models in the fallback chain failed:\n" + "\n".join(attempted))
        raise last_error

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        def call(model):
            response = self.client.models.generate_content(
                model=model,
                contents=user_prompt,
                config={"system_instruction": system_prompt},
            )
            return response.text
        return self._call_with_fallback(call)

    def run_agentic_task(self, system_prompt: str, task_prompt: str, tools: list[Callable], building_id: str = "BLD-HQ-01") -> dict:
        """
        Real agentic execution: passes the tool functions directly to
        Gemini. The SDK's Automatic Function Calling (AFC) lets the model
        decide which tools to call and in what order — it calls them,
        feeds results back to the model, and loops until the model returns
        a final answer (default cap: 10 remote calls).
        """
        from google.genai import types

        system_prompt = system_prompt + (
            f"\n\nIMPORTANT: every tool below takes a building_id argument — always pass exactly "
            f'building_id="{building_id}" (the building actually being investigated), never a '
            "different value, even if a tool's own docstring shows a different example."
        )

        def call(model):
            response = self.client.models.generate_content(
                model=model,
                contents=task_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=tools,
                ),
            )

            trace = []
            history = getattr(response, "automatic_function_calling_history", None) or []
            for content in history:
                for part in getattr(content, "parts", []) or []:
                    fc = getattr(part, "function_call", None)
                    fr = getattr(part, "function_response", None)
                    if fc:
                        trace.append({"tool": fc.name, "args": dict(fc.args or {}), "result": None})
                    elif fr and trace:
                        trace[-1]["result"] = fr.response

            return {"final_text": response.text, "tool_calls": trace}

        return self._call_with_fallback(call)
