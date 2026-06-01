import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from backend.app.rag.metadata_tools import (
    get_creator_info,
    get_engagement_comparison,
    get_session_video_summary,
    get_video_metrics,
)
from backend.app.store.postgres import get_chat_messages, get_video_metadata
from backend.app.store.vector import retrieve

METADATA_TERMS = {
    "engagement",
    "rate",
    "creator",
    "follower",
    "followers",
    "views",
    "view",
    "likes",
    "like",
    "comments",
    "comment",
    "count",
    "counts",
    "metric",
    "metrics",
    "duration",
    "upload",
    "hashtag",
    "hashtags",
}
TRANSCRIPT_TERMS = {
    "compare",
    "comparison",
    "discuss",
    "discusses",
    "topic",
    "about",
    "say",
    "says",
    "said",
    "mention",
    "mentions",
    "transcript",
    "chunk",
    "hook",
    "opening",
    "first 5",
    "first five",
    "message",
    "content",
    "explain",
    "why",
    "improve",
    "recommend",
    "recommendation",
}


class CreatorSessionState(TypedDict, total=False):
    session_id: str
    query: str
    route: str
    history: list[dict]
    metadata: list[dict]
    metadata_tool_results: list[dict]
    chunks: list[dict]
    sources: list[dict]


def _detect_video_ids(query: str) -> set[str]:
    lowered = query.lower()
    video_ids = set()
    if "video a" in lowered:
        video_ids.add("A")
    if "video b" in lowered:
        video_ids.add("B")
    if re.search(r"\bA\b", query) and re.search(r"\bB\b", query):
        video_ids.update({"A", "B"})
    return video_ids


def _detect_hook_only(query: str) -> bool:
    lowered = query.lower()
    return "hook" in lowered or "first 5" in lowered or "first five" in lowered


def _has_any_term(query: str, terms: set[str]) -> bool:
    lowered = query.lower()
    return any(term in lowered for term in terms)


def classify_query(query: str) -> str:
    has_metadata = _has_any_term(query, METADATA_TERMS)
    has_transcript = _has_any_term(query, TRANSCRIPT_TERMS)
    video_ids = _detect_video_ids(query)
    if len(video_ids) == 2 and has_transcript:
        return "mixed"
    if has_metadata and has_transcript:
        return "mixed"
    if has_metadata:
        return "metadata"
    return "semantic"


def classify_question(state: CreatorSessionState) -> CreatorSessionState:
    return {"route": classify_query(state["query"])}


def load_history(state: CreatorSessionState) -> CreatorSessionState:
    return {"history": get_chat_messages(state["session_id"], limit=12)}


def retrieve_metadata(state: CreatorSessionState) -> CreatorSessionState:
    return {"metadata": get_video_metadata(state["session_id"])}


def _creator_info_results(session_id: str, video_ids: set[str]) -> list[dict]:
    if video_ids:
        return [get_creator_info(session_id, video_id) for video_id in sorted(video_ids)]
    return [get_creator_info(session_id, video_id) for video_id in ("A", "B")]


def run_metadata_tools(state: CreatorSessionState) -> CreatorSessionState:
    query = state["query"]
    lowered = query.lower()
    session_id = state["session_id"]
    video_ids = _detect_video_ids(query)
    results: list[dict] = []

    if "engagement" in lowered:
        results.append({"tool": "get_engagement_comparison", "result": get_engagement_comparison(session_id)})
    if any(term in lowered for term in ("creator", "follower", "followers")):
        results.append({"tool": "get_creator_info", "result": _creator_info_results(session_id, video_ids)})
    if any(
        term in lowered
        for term in (
            "view",
            "views",
            "like",
            "likes",
            "comment",
            "comments",
            "metric",
            "metrics",
            "count",
            "counts",
            "duration",
        )
    ):
        results.append({"tool": "get_video_metrics", "result": get_video_metrics(session_id)})
    if not results:
        results.append({"tool": "get_session_video_summary", "result": get_session_video_summary(session_id)})

    return {"metadata_tool_results": results}


def retrieve_chunks(state: CreatorSessionState) -> CreatorSessionState:
    if state.get("route") == "metadata":
        return {"chunks": []}

    query = state["query"]
    video_ids = _detect_video_ids(query)
    hook_only = _detect_hook_only(query)
    if len(video_ids) == 2:
        chunks = []
        for video_id in ("A", "B"):
            chunks.extend(
                retrieve(
                    query=query,
                    session_id=state["session_id"],
                    video_id=video_id,
                    hook_only=hook_only,
                    top_k=4 if hook_only else 3,
                )
            )
        return {"chunks": chunks}

    video_id = next(iter(video_ids), None)
    return {
        "chunks": retrieve(
            query=query,
            session_id=state["session_id"],
            video_id=video_id,
            hook_only=hook_only,
            top_k=8 if hook_only else 6,
        )
    }


def build_graph():
    graph = StateGraph(CreatorSessionState)
    graph.add_node("classify_question", classify_question)
    graph.add_node("load_history", load_history)
    graph.add_node("retrieve_metadata", retrieve_metadata)
    graph.add_node("run_metadata_tools", run_metadata_tools)
    graph.add_node("retrieve_chunks", retrieve_chunks)
    graph.set_entry_point("classify_question")
    graph.add_edge("classify_question", "load_history")
    graph.add_edge("load_history", "retrieve_metadata")
    graph.add_edge("retrieve_metadata", "run_metadata_tools")
    graph.add_edge("run_metadata_tools", "retrieve_chunks")
    graph.add_edge("retrieve_chunks", END)
    return graph.compile()


_graph = build_graph()


def run_retrieval_graph(session_id: str, query: str) -> CreatorSessionState:
    return _graph.invoke({"session_id": session_id, "query": query})
