import json
import logging
from collections.abc import Iterator

from backend.app.core.app_errors import classify_chat_error
from backend.app.core.config import get_settings
from backend.app.rag.chat_client import ChatUsage, estimate_message_tokens, estimate_text_tokens, stream_chat_events
from backend.app.rag.graph import run_retrieval_graph
from backend.app.rag.prompt import build_chat_messages, build_sources
from backend.app.store.postgres import append_chat_message, record_chat_usage

logger = logging.getLogger(__name__)


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def stream_rag_response(session_id: str, message: str) -> Iterator[str]:
    full_response = ""
    route = None
    retrieval_policy = None
    usage: ChatUsage | None = None
    streamed_model: str | None = None
    stage = "retrieval"
    try:
        state = run_retrieval_graph(session_id=session_id, query=message)
        resolved_message = state.get("resolved_query") or message
        route = state.get("route", "TRANSCRIPT_ONLY")
        retrieval_policy = state.get("retrieval_policy")
        metadata = state.get("metadata", [])
        metadata_tool_results = state.get("metadata_tool_results", [])
        chunks = state.get("chunks", [])
        history = state.get("history", [])
        sources = build_sources(metadata, chunks)
        stage = "prompt"
        messages = build_chat_messages(
            resolved_message,
            metadata,
            metadata_tool_results,
            chunks,
            history,
            route,
        )

        stage = "persistence"
        append_chat_message(session_id=session_id, role="user", content=message)

        stage = "provider"
        yield _sse("sources", {"sources": sources, "route": route, "retrieval_policy": retrieval_policy})
        for event in stream_chat_events(messages):
            streamed_model = event.model or streamed_model
            if event.usage:
                usage = event.usage
                continue
            if event.token:
                full_response += event.token
                yield _sse("token", {"token": event.token})
        stage = "persistence"
        append_chat_message(
            session_id=session_id,
            role="assistant",
            content=full_response,
            sources=sources,
        )
        prompt_tokens = usage.prompt_tokens if usage else estimate_message_tokens(messages)
        completion_tokens = usage.completion_tokens if usage else estimate_text_tokens(full_response)
        record_chat_usage(
            session_id=session_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            llm_model=streamed_model or get_settings().groq_chat_model,
        )
        yield _sse("done", {"ok": True, "route": route, "retrieval_policy": retrieval_policy})
    except Exception as exc:
        error = classify_chat_error(exc, stage=stage)
        logger.exception("Chat stream failed session_id=%s route=%s", session_id, route or "unavailable")
        yield _sse(
            "error",
            {
                "error": error.to_dict(),
                "message": error.message,
                "route": route,
                "retrieval_policy": retrieval_policy,
            },
        )
