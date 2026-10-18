"""Groq tool investigations with bounded calls and no replay after side effects.
Tool results are streamed as they finish; the final model response is emitted once.
"""
import os
import json
import inspect
import time
from typing import Callable
from app.services.ai_providers.base import AIProvider
from app.services.ai_providers.tool_schema import function_to_tool_schema

MAX_AGENT_ITERATIONS = 8
MODEL_FALLBACK_CHAIN = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]


class GroqProvider(AIProvider):
    def __init__(self, model: str | None = None):
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        self.client = Groq(api_key=api_key, timeout=12.0, max_retries=0)
        self.model = model or os.getenv("GROQ_MODEL") or MODEL_FALLBACK_CHAIN[0]
        self._models_to_try = [self.model] + [m for m in MODEL_FALLBACK_CHAIN if m != self.model]

    def _call_with_fallback(self, fn):
        for index, model in enumerate(self._models_to_try):
            try:
                result = fn(model)
                self.model = model
                return result
            except Exception as exc:
                # A different model cannot repair credentials, a network outage,
                # or quota exhaustion. Only model availability warrants fallback.
                body = getattr(exc, "body", {}) or {}
                error = body.get("error", body) if isinstance(body, dict) else {}
                code = error.get("code") if isinstance(error, dict) else None
                if code not in {"model_decommissioned", "model_not_found"} or index == len(self._models_to_try) - 1:
                    raise

    def _completion(self, model, messages, **kwargs):
        options = dict(model=model, messages=messages, max_completion_tokens=1024, **kwargs)
        if model.startswith('openai/gpt-oss-'):
            options['reasoning_effort'] = 'low'
        try:
            return self.client.chat.completions.create(**options)
        except Exception as exc:
            headers = getattr(getattr(exc, 'response', None), 'headers', {})
            try:
                delay = float(headers.get('retry-after', '0'))
            except (TypeError, ValueError):
                delay = 0
            if getattr(exc, 'status_code', None) == 429 and 0 < delay <= 10:
                time.sleep(delay)
                return self.client.chat.completions.create(**options)
            raise

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        response = self._call_with_fallback(lambda model: self._completion(model, messages))
        return response.choices[0].message.content or ""

    def run_agentic_task(self, system_prompt: str, task_prompt: str, tools: list[Callable], building_id="BLD-HQ-01") -> dict:
        for event in self.run_agentic_task_stream(system_prompt, task_prompt, tools, building_id):
            if event["type"] == "done":
                return {"final_text": event["final_text"], "tool_calls": event["tool_calls"]}
        raise RuntimeError("Investigation ended without a result")

    def run_agentic_task_stream(self, system_prompt: str, task_prompt: str, tools: list[Callable], building_id="BLD-HQ-01"):
        tool_map = {tool.__name__: tool for tool in tools}
        schemas = [function_to_tool_schema(tool) for tool in tools]
        messages = [
            {"role": "system", "content": system_prompt + f"\nInvestigate building {building_id}. Use that building_id only on tools that accept it. Request independent read-only tools together in one response to avoid redundant round trips. Use results before deciding on any write action. Give a concise final summary. Do not repeat successful write actions."},
            {"role": "user", "content": task_prompt},
        ]
        options = {"tools": schemas, "tool_choice": "auto"} if schemas else {}
        # Fallback is allowed only before any tool can have changed data.
        response = self._call_with_fallback(lambda model: self._completion(model, messages, **options))
        trace = []
        for _ in range(MAX_AGENT_ITERATIONS):
            message = response.choices[0].message
            if not message.tool_calls:
                final_text = message.content or "No additional findings were returned."
                yield {"type": "token", "text": final_text}
                yield {"type": "done", "tool_calls": trace, "final_text": final_text}
                return
            messages.append({"role": "assistant", "content": message.content, "tool_calls": [call.model_dump() for call in message.tool_calls]})
            for call in message.tool_calls:
                name = call.function.name
                args = {}
                try:
                    args = json.loads(call.function.arguments or "{}")
                    if not isinstance(args, dict):
                        raise ValueError("Tool arguments must be an object")
                    if name not in tool_map:
                        raise ValueError(f"Unknown tool: {name}")
                    if "building_id" in inspect.signature(tool_map[name]).parameters:
                        args["building_id"] = building_id
                    inspect.signature(tool_map[name]).bind(**args)
                except (ValueError, TypeError) as exc:
                    result = {"error": str(exc)}
                else:
                    # Do not retry a tool when it raises: a side effect may
                    # already have committed before the exception.
                    result = tool_map[name](**args)
                record = {"tool": name, "args": args, "result": result}
                trace.append(record)
                yield {"type": "tool_call", **record}
                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, default=str)})
            response = self._completion(self.model, messages, **options)
        final_text = "Investigation reached its step limit. Review the collected tool results before running again."
        yield {"type": "token", "text": final_text}
        yield {"type": "done", "tool_calls": trace, "final_text": final_text}
