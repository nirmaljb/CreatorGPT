from typing import TypedDict

from langgraph.graph import END, StateGraph

from backend.app.store.postgres import get_chat_messages, get_video_metadata
from backend.app.store.vector import retrieve


class CreatorSessionState(TypedDict, total=False):
    session_id: str
    query: str
    history: list[dict]
    metadata: list[dict]
    chunks: list[dict]
    sources: list[dict]


def _detect_video_ids(query: str) -> set[str]:
    lowered = query.lower()
    video_ids = set()
    if "video a" in lowered:
        video_ids.add("A")
    if "video b" in lowered:
        video_ids.add("B")
    return video_ids


def _detect_hook_only(query: str) -> bool:
    lowered = query.lower()
    return "hook" in lowered or "first 5" in lowered or "first five" in lowered


def load_history(state: CreatorSessionState) -> CreatorSessionState:
    return {"history": get_chat_messages(state["session_id"], limit=12)}


def retrieve_metadata(state: CreatorSessionState) -> CreatorSessionState:
    return {"metadata": get_video_metadata(state["session_id"])}


def retrieve_chunks(state: CreatorSessionState) -> CreatorSessionState:
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
    graph.add_node("load_history", load_history)
    graph.add_node("retrieve_metadata", retrieve_metadata)
    graph.add_node("retrieve_chunks", retrieve_chunks)
    graph.set_entry_point("load_history")
    graph.add_edge("load_history", "retrieve_metadata")
    graph.add_edge("retrieve_metadata", "retrieve_chunks")
    graph.add_edge("retrieve_chunks", END)
    return graph.compile()


_graph = build_graph()


def run_retrieval_graph(session_id: str, query: str) -> CreatorSessionState:
    return _graph.invoke({"session_id": session_id, "query": query})
