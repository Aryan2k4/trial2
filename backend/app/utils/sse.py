"""
Tiny shared helper for turning a generator of dict events into a
Server-Sent Events HTTP response — used by every domain's
/investigate/stream endpoint so each router doesn't reimplement the same
SSE framing.
"""
import json
from typing import Generator
from fastapi.responses import StreamingResponse


def _format_sse(events: Generator[dict, None, None]):
    try:
        for event in events:
            yield f"data: {json.dumps(event, default=str)}\n\n"
    except Exception as e:
        # Never let an unexpected mid-stream error just hang the
        # connection open with no explanation — surface it as one last
        # event the frontend can render, then let the stream close.
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


def sse_stream_response(events: Generator[dict, None, None]) -> StreamingResponse:
    return StreamingResponse(
        _format_sse(events),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Disables buffering on nginx-style proxies (incl. some PaaS
            # setups like Render) that would otherwise hold the whole
            # response until it's complete, defeating the point of SSE.
            "X-Accel-Buffering": "no",
        },
    )
