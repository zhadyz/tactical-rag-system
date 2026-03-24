"""
Forge - SSE Streaming Generator

Wraps the agent's async generator into Server-Sent Event format.
Emits all event types defined in the Forge streaming protocol:
  agent_thinking, tool_call, tool_result, crag_evaluation,
  retrieval_complete, token, sources, verification, metadata, done, error
"""

import json
import logging
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)


class ForgeStreamGenerator:
    """
    Converts internal stream events into SSE-formatted lines.

    Usage:
        generator = ForgeStreamGenerator()
        async for line in generator.wrap(agent_stream):
            # Each line is "data: {json}\\n\\n"
            yield line  # inside a StreamingResponse
    """

    async def wrap(
        self, event_stream: AsyncGenerator[dict[str, Any], None]
    ) -> AsyncGenerator[str, None]:
        """
        Consume the agent event stream and yield SSE-formatted strings.

        Each yielded string is a complete SSE data line:
            data: {"type": "...", "content": ...}\n\n

        Handles errors gracefully -- emits an error event then done.
        """
        try:
            async for event in event_stream:
                event_type = event.get("type", "unknown")
                content = event.get("content")

                yield self._format(event_type, content)

        except Exception as e:
            logger.error(f"[StreamGenerator] Error during streaming: {e}", exc_info=True)
            yield self._format("error", str(e))
            yield self._format("done", None)

    # ------------------------------------------------------------------
    # Convenience emitters (used by the agent to build events)
    # ------------------------------------------------------------------

    @staticmethod
    def event(event_type: str, content: Any = None) -> dict[str, Any]:
        """Build an internal event dict."""
        return {"type": event_type, "content": content}

    @staticmethod
    def thinking(message: str) -> dict[str, Any]:
        return {"type": "agent_thinking", "content": message}

    @staticmethod
    def tool_call(call_id: str, tool_name: str, tool_input: dict) -> dict[str, Any]:
        return {
            "type": "tool_call",
            "content": {
                "id": call_id,
                "tool": tool_name,
                "input": tool_input,
            },
        }

    @staticmethod
    def tool_result(
        result_id: str,
        call_id: str,
        count: int = 0,
        top_score: float = 0.0,
        duration_ms: float = 0.0,
    ) -> dict[str, Any]:
        return {
            "type": "tool_result",
            "content": {
                "id": result_id,
                "tool_call_id": call_id,
                "count": count,
                "top_score": top_score,
                "duration_ms": duration_ms,
            },
        }

    @staticmethod
    def crag_evaluation(evaluations: list[dict]) -> dict[str, Any]:
        return {"type": "crag_evaluation", "content": evaluations}

    @staticmethod
    def retrieval_complete(total_docs: int, stages: list[dict]) -> dict[str, Any]:
        return {
            "type": "retrieval_complete",
            "content": {"total_docs": total_docs, "stages": stages},
        }

    @staticmethod
    def token(text: str) -> dict[str, Any]:
        return {"type": "token", "content": text}

    @staticmethod
    def sources(source_list: list[dict]) -> dict[str, Any]:
        return {"type": "sources", "content": source_list}

    @staticmethod
    def verification(results: list[dict]) -> dict[str, Any]:
        return {"type": "verification", "content": results}

    @staticmethod
    def metadata(data: dict) -> dict[str, Any]:
        return {"type": "metadata", "content": data}

    @staticmethod
    def done() -> dict[str, Any]:
        return {"type": "done", "content": None}

    @staticmethod
    def error(message: str) -> dict[str, Any]:
        return {"type": "error", "content": message}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _format(event_type: str, content: Any) -> str:
        """Format a single SSE data line."""
        payload = {"type": event_type}
        if content is not None:
            payload["content"] = content
        return f"data: {json.dumps(payload, default=str)}\n\n"
