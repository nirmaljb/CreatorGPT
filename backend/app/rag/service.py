import json
from collections.abc import Iterator

from backend.app.rag.chat_client import stream_chat_completion
from backend.app.rag.graph import run_retrieval_graph
from backend.app.rag.prompt import build_chat_messages, build_sources
from backend.app.store.postgres import append_chat_message


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def stream_rag_response(session_id: str, message: str) -> Iterator[str]:
    state = run_retrieval_graph(session_id=session_id, query=message)
    resolved_message = state.get("resolved_query") or message
    metadata = state.get("metadata", [])
    metadata_tool_results = state.get("metadata_tool_results", [])
    chunks = state.get("chunks", [])
    history = state.get("history", [])
    sources = build_sources(metadata, chunks)
    messages = build_chat_messages(
        resolved_message,
        metadata,
        metadata_tool_results,
        chunks,
        history,
        state.get("route", "TRANSCRIPT_ONLY"),
    )

    append_chat_message(session_id=session_id, role="user", content=message)

    full_response = ""
    yield _sse("sources", {"sources": sources})
    try:
        for token in stream_chat_completion(messages):
            full_response += token
            yield _sse("token", {"token": token})
        append_chat_message(
            session_id=session_id,
            role="assistant",
            content=full_response,
            sources=sources,
        )
        yield _sse("done", {"ok": True})
    except Exception as exc:
        yield _sse("error", {"message": str(exc)})
