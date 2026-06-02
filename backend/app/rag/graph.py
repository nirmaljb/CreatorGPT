import logging
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from backend.app.core.config import get_settings
from backend.app.rag.metadata_tools import (
    get_creator_info,
    get_engagement_comparison,
    get_session_video_summary,
    get_video_metrics,
)
from backend.app.store.postgres import get_chat_messages, get_video_metadata
from backend.app.store.vector import retrieve

logger = logging.getLogger(__name__)

METADATA_ONLY = "METADATA_ONLY"
TRANSCRIPT_ONLY = "TRANSCRIPT_ONLY"
HOOK_COMPARISON = "HOOK_COMPARISON"
MIXED_COMPARISON = "MIXED_COMPARISON"
IMPROVEMENT_SUGGESTION = "IMPROVEMENT_SUGGESTION"
FOLLOW_UP = "FOLLOW_UP"

HOOK_RETRIEVAL = "hook_retrieval"
VIDEO_A_RETRIEVAL = "video_a_retrieval"
VIDEO_B_RETRIEVAL = "video_b_retrieval"
COMPARISON_RETRIEVAL = "comparison_retrieval"
METADATA_AUGMENTED_RETRIEVAL = "metadata_augmented_retrieval"

METADATA_TOOL_ROUTES = {METADATA_ONLY, MIXED_COMPARISON, IMPROVEMENT_SUGGESTION}
CHUNK_ROUTES = {TRANSCRIPT_ONLY, HOOK_COMPARISON, MIXED_COMPARISON, IMPROVEMENT_SUGGESTION}
BALANCED_TOP_K_PER_VIDEO = 4
DEFAULT_TRANSCRIPT_TOP_K = 6

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
    "share",
    "shares",
    "save",
    "saves",
    "stat",
    "stats",
    "scorecard",
}
CONTENT_TERMS = {
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
    "opening",
    "message",
    "content",
    "explain",
    "story",
    "tone",
    "pacing",
}
HOOK_TERMS = {"hook", "hooks", "first 5", "first five", "opening", "intro"}
IMPROVEMENT_TERMS = {
    "change",
    "changes",
    "fix",
    "improve",
    "improvement",
    "improvements",
    "recommend",
    "recommendation",
    "remake",
    "suggest",
}
COMPARISON_TERMS = {"compare", "comparison", "versus", "vs", "better", "worse", "more", "less", "higher", "lower"}
CAUSAL_TERMS = {"why", "reason", "reasons", "because", "drove", "drive", "worked", "perform", "performed"}
PERFORMANCE_TERMS = {"engagement", "views", "likes", "comments", "performance"}
IMPLICIT_TWO_VIDEO_TERMS = {
    "both",
    "both videos",
    "both of them",
    "each video",
    "either video",
    "one of these",
    "the two videos",
    "these two",
    "which one",
    "which video",
}
FOLLOW_UP_PREFIXES = (
    "what about",
    "how about",
    "and ",
    "also",
    "then",
    "what is their",
    "what's their",
    "their ",
)
FOLLOW_UP_PRONOUN_TERMS = {"their", "that video", "this video", "it", "that one", "this one", "the other one"}


class CreatorSessionState(TypedDict, total=False):
    session_id: str
    query: str
    resolved_query: str
    route: str
    initial_route: str
    history: list[dict]
    metadata: list[dict]
    metadata_tool_results: list[dict]
    chunks: list[dict]
    sources: list[dict]
    retrieval_policy: str


def _detect_video_ids(query: str) -> set[str]:
    lowered = query.lower()
    video_ids = set()
    if re.search(r"\bvideo\s+a\b", lowered) or re.search(r"\bA\b", query):
        video_ids.add("A")
    if re.search(r"\bvideo\s+b\b", lowered) or re.search(r"\bB\b", query):
        video_ids.add("B")
    return video_ids


def _max_retrieved_chunks() -> int:
    return max(1, get_settings().max_retrieved_chunks)


def _single_video_top_k(default_top_k: int) -> int:
    return max(1, min(default_top_k, _max_retrieved_chunks()))


def _balanced_top_k_per_video(default_top_k: int = BALANCED_TOP_K_PER_VIDEO) -> int:
    return max(1, min(default_top_k, max(1, _max_retrieved_chunks() // 2)))


def _cap_retrieved_chunks(chunks: list[dict]) -> list[dict]:
    max_chunks = _max_retrieved_chunks()
    if len(chunks) <= max_chunks:
        return chunks
    logger.warning(
        "Applied retrieval backpressure retrieved_count=%s max_retrieved_chunks=%s",
        len(chunks),
        max_chunks,
    )
    return chunks[:max_chunks]


def _detect_hook_only(query: str) -> bool:
    lowered = query.lower()
    return any(term in lowered for term in HOOK_TERMS)


def _has_any_term(query: str, terms: set[str]) -> bool:
    lowered = query.lower()
    return any(term in lowered for term in terms)


def _is_implicit_two_video_query(query: str) -> bool:
    lowered = query.lower()
    return any(term in lowered for term in IMPLICIT_TWO_VIDEO_TERMS)


def _last_user_query(history: list[dict] | None) -> str | None:
    for item in reversed(history or []):
        if item.get("role") == "user" and item.get("content"):
            return str(item["content"])
    return None


def _last_referenced_video_ids(history: list[dict] | None) -> set[str]:
    for item in reversed(history or []):
        content = str(item.get("content") or "")
        video_ids = _detect_video_ids(content)
        if video_ids:
            return video_ids
    return set()


def _is_follow_up_query(query: str, history: list[dict] | None) -> bool:
    if not history:
        return False
    lowered = query.lower().strip()
    if lowered.startswith(FOLLOW_UP_PREFIXES):
        return True
    return any(term in lowered for term in FOLLOW_UP_PRONOUN_TERMS) and bool(_last_referenced_video_ids(history))


def _is_performance_causal_question(query: str, video_ids: set[str]) -> bool:
    has_causal = _has_any_term(query, CAUSAL_TERMS)
    has_performance = _has_any_term(query, PERFORMANCE_TERMS)
    has_comparison = _has_any_term(query, COMPARISON_TERMS) or len(video_ids) == 2
    return has_causal and has_performance and has_comparison


def classify_query(query: str, history: list[dict] | None = None, allow_follow_up: bool = True) -> str:
    if allow_follow_up and _is_follow_up_query(query, history):
        return FOLLOW_UP

    video_ids = _detect_video_ids(query)
    has_metadata = _has_any_term(query, METADATA_TERMS)
    has_content = _has_any_term(query, CONTENT_TERMS)
    has_comparison = _has_any_term(query, COMPARISON_TERMS)

    if _has_any_term(query, IMPROVEMENT_TERMS):
        return IMPROVEMENT_SUGGESTION
    if _detect_hook_only(query):
        return HOOK_COMPARISON
    if _is_performance_causal_question(query, video_ids):
        return MIXED_COMPARISON
    if has_metadata and not has_content:
        return METADATA_ONLY
    if has_metadata and (has_content or has_comparison):
        return MIXED_COMPARISON
    return TRANSCRIPT_ONLY


def _replace_video_reference(query: str, video_id: str) -> str:
    replaced = re.sub(r"\b[Vv]ideo\s+[ABab]\b", f"Video {video_id}", query)
    replaced = re.sub(r"\b[AB]\b", video_id, replaced)
    if replaced != query:
        return replaced
    return f"{query.rstrip('?. ')} for Video {video_id}?"


def _opposite_video_id(video_ids: set[str]) -> str | None:
    if video_ids == {"A"}:
        return "B"
    if video_ids == {"B"}:
        return "A"
    return None


def resolve_follow_up_query(query: str, history: list[dict] | None = None) -> str:
    lowered = query.lower().strip()
    explicit_video_ids = _detect_video_ids(query)
    previous_video_ids = _last_referenced_video_ids(history)
    previous_user_query = _last_user_query(history)

    if "other" in lowered:
        other_id = _opposite_video_id(previous_video_ids)
        if other_id and previous_user_query:
            return _replace_video_reference(previous_user_query, other_id)
        if other_id:
            return f"{query.rstrip('?. ')} for Video {other_id}?"

    if explicit_video_ids and previous_user_query and lowered.startswith(("what about", "how about", "and ")):
        return _replace_video_reference(previous_user_query, sorted(explicit_video_ids)[0])

    if not explicit_video_ids and previous_video_ids:
        video_text = " and ".join(f"Video {video_id}" for video_id in sorted(previous_video_ids))
        return f"{query.rstrip('?. ')} for {video_text}?"

    if explicit_video_ids:
        video_text = " and ".join(f"Video {video_id}" for video_id in sorted(explicit_video_ids))
        return f"{query.rstrip('?. ')} for {video_text}?"

    return query


def classify_question(state: CreatorSessionState) -> CreatorSessionState:
    route = classify_query(state["query"], history=state.get("history", []))
    logger.info("Classified chat query route=%s query=%s", route, state["query"])
    return {"route": route, "initial_route": route, "resolved_query": state["query"]}


def resolve_follow_up(state: CreatorSessionState) -> CreatorSessionState:
    resolved_query = resolve_follow_up_query(state["query"], state.get("history", []))
    route = classify_query(resolved_query, allow_follow_up=False)
    logger.info(
        "Resolved follow-up query route=%s original_query=%s resolved_query=%s",
        route,
        state["query"],
        resolved_query,
    )
    return {"route": route, "resolved_query": resolved_query}


def load_history(state: CreatorSessionState) -> CreatorSessionState:
    return {"history": get_chat_messages(state["session_id"], limit=get_settings().max_chat_history_messages)}


def retrieve_metadata(state: CreatorSessionState) -> CreatorSessionState:
    return {"metadata": get_video_metadata(state["session_id"])}


def _creator_info_results(session_id: str, video_ids: set[str]) -> list[dict]:
    if video_ids:
        return [get_creator_info(session_id, video_id) for video_id in sorted(video_ids)]
    return [get_creator_info(session_id, video_id) for video_id in ("A", "B")]


def _append_tool_result(results: list[dict], tool: str, result: object) -> None:
    if not any(item["tool"] == tool for item in results):
        results.append({"tool": tool, "result": result})


def run_metadata_tools(state: CreatorSessionState) -> CreatorSessionState:
    query = state.get("resolved_query") or state["query"]
    lowered = query.lower()
    route = state.get("route", TRANSCRIPT_ONLY)
    session_id = state["session_id"]
    video_ids = _detect_video_ids(query)
    results: list[dict] = []

    if "engagement" in lowered or route in {MIXED_COMPARISON, IMPROVEMENT_SUGGESTION}:
        _append_tool_result(results, "get_engagement_comparison", get_engagement_comparison(session_id))
    if any(term in lowered for term in ("creator", "follower", "followers")):
        _append_tool_result(results, "get_creator_info", _creator_info_results(session_id, video_ids))
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
        _append_tool_result(results, "get_video_metrics", get_video_metrics(session_id))
    if route == IMPROVEMENT_SUGGESTION or not results:
        _append_tool_result(results, "get_session_video_summary", get_session_video_summary(session_id))

    logger.info(
        "Ran metadata tools route=%s session_id=%s tools=%s",
        route,
        session_id,
        [item["tool"] for item in results],
    )
    return {"metadata_tool_results": results}


def _comparison_video_ids(query: str, route: str) -> set[str]:
    detected = _detect_video_ids(query)
    if route == IMPROVEMENT_SUGGESTION:
        return detected | {"A", "B"}
    if route in {HOOK_COMPARISON, MIXED_COMPARISON}:
        return detected or {"A", "B"}
    if route == TRANSCRIPT_ONLY and _is_implicit_two_video_query(query):
        return detected or {"A", "B"}
    return detected


def _retrieve_for_video(query: str, session_id: str, video_id: str, hook_only: bool, top_k: int) -> list[dict]:
    return retrieve(query=query, session_id=session_id, video_id=video_id, hook_only=hook_only, top_k=top_k)


def hook_retrieval(
    query: str,
    session_id: str,
    video_id: str | None = None,
    top_k: int | None = None,
) -> list[dict]:
    resolved_top_k = _single_video_top_k(top_k or BALANCED_TOP_K_PER_VIDEO)
    logger.info(
        "Applying retrieval policy=%s session_id=%s video_id=%s top_k=%s",
        HOOK_RETRIEVAL,
        session_id,
        video_id or "any",
        resolved_top_k,
    )
    return retrieve(query=query, session_id=session_id, video_id=video_id, hook_only=True, top_k=resolved_top_k)


def video_a_retrieval(query: str, session_id: str, top_k: int | None = None) -> list[dict]:
    resolved_top_k = _single_video_top_k(top_k or BALANCED_TOP_K_PER_VIDEO)
    logger.info(
        "Applying retrieval policy=%s session_id=%s top_k=%s",
        VIDEO_A_RETRIEVAL,
        session_id,
        resolved_top_k,
    )
    return _retrieve_for_video(query, session_id, "A", False, resolved_top_k)


def video_b_retrieval(query: str, session_id: str, top_k: int | None = None) -> list[dict]:
    resolved_top_k = _single_video_top_k(top_k or BALANCED_TOP_K_PER_VIDEO)
    logger.info(
        "Applying retrieval policy=%s session_id=%s top_k=%s",
        VIDEO_B_RETRIEVAL,
        session_id,
        resolved_top_k,
    )
    return _retrieve_for_video(query, session_id, "B", False, resolved_top_k)


def comparison_retrieval(
    query: str,
    session_id: str,
    hook_only: bool = False,
    top_k_per_video: int | None = None,
) -> list[dict]:
    resolved_top_k = _balanced_top_k_per_video(top_k_per_video or BALANCED_TOP_K_PER_VIDEO)
    logger.info(
        "Applying retrieval policy=%s session_id=%s hook_only=%s top_k_per_video=%s",
        COMPARISON_RETRIEVAL,
        session_id,
        hook_only,
        resolved_top_k,
    )
    chunks = []
    for video_id in ("A", "B"):
        if hook_only:
            chunks.extend(hook_retrieval(query, session_id, video_id, resolved_top_k))
        else:
            chunks.extend(_retrieve_for_video(query, session_id, video_id, False, resolved_top_k))
    return _cap_retrieved_chunks(chunks)


def metadata_augmented_retrieval(query: str, session_id: str, video_ids: set[str]) -> list[dict]:
    top_k = _single_video_top_k(BALANCED_TOP_K_PER_VIDEO) if len(video_ids) == 1 else _balanced_top_k_per_video()
    logger.info(
        "Applying retrieval policy=%s session_id=%s video_ids=%s top_k_per_video=%s",
        METADATA_AUGMENTED_RETRIEVAL,
        session_id,
        sorted(video_ids) or ["A", "B"],
        top_k,
    )
    if len(video_ids) == 1:
        video_id = next(iter(video_ids))
        if video_id == "A":
            return video_a_retrieval(query, session_id, top_k)
        if video_id == "B":
            return video_b_retrieval(query, session_id, top_k)
    return comparison_retrieval(query, session_id, hook_only=False, top_k_per_video=top_k)


def retrieve_chunks(state: CreatorSessionState) -> CreatorSessionState:
    route = state.get("route", TRANSCRIPT_ONLY)
    if route not in CHUNK_ROUTES:
        return {"chunks": [], "retrieval_policy": "none"}

    query = state.get("resolved_query") or state["query"]
    session_id = state["session_id"]

    if route == IMPROVEMENT_SUGGESTION:
        top_k_per_video = _balanced_top_k_per_video()
        chunks = video_a_retrieval(
            f"{query} strong evidence what worked well engaging hook clarity",
            session_id,
            top_k_per_video,
        )
        chunks.extend(
            video_b_retrieval(
                f"{query} improvement opportunity weak hook unclear pacing missing context",
                session_id,
                top_k_per_video,
            )
        )
        return {"chunks": _cap_retrieved_chunks(chunks), "retrieval_policy": METADATA_AUGMENTED_RETRIEVAL}

    hook_only = route == HOOK_COMPARISON
    video_ids = _comparison_video_ids(query, route)
    if len(video_ids) == 2:
        if route == MIXED_COMPARISON:
            return {
                "chunks": metadata_augmented_retrieval(query, session_id, video_ids),
                "retrieval_policy": METADATA_AUGMENTED_RETRIEVAL,
            }
        return {
            "chunks": comparison_retrieval(query, session_id, hook_only=hook_only),
            "retrieval_policy": HOOK_RETRIEVAL if hook_only else COMPARISON_RETRIEVAL,
        }

    video_id = next(iter(video_ids), None)
    if route == MIXED_COMPARISON:
        return {
            "chunks": metadata_augmented_retrieval(query, session_id, video_ids),
            "retrieval_policy": METADATA_AUGMENTED_RETRIEVAL,
        }
    if hook_only:
        return {
            "chunks": hook_retrieval(query, session_id, video_id),
            "retrieval_policy": HOOK_RETRIEVAL,
        }
    return {
        "chunks": retrieve(
            query=query,
            session_id=session_id,
            video_id=video_id,
            hook_only=False,
            top_k=_single_video_top_k(DEFAULT_TRANSCRIPT_TOP_K),
        ),
        "retrieval_policy": VIDEO_A_RETRIEVAL
        if video_id == "A"
        else VIDEO_B_RETRIEVAL
        if video_id == "B"
        else "transcript_retrieval",
    }


def _after_classification(state: CreatorSessionState) -> str:
    return "resolve_follow_up" if state.get("route") == FOLLOW_UP else "retrieve_metadata"


def _after_metadata(state: CreatorSessionState) -> str:
    return "run_metadata_tools" if state.get("route") in METADATA_TOOL_ROUTES else "retrieve_chunks"


def _after_metadata_tools(state: CreatorSessionState) -> str:
    return "end" if state.get("route") == METADATA_ONLY else "retrieve_chunks"


def build_graph():
    graph = StateGraph(CreatorSessionState)
    graph.add_node("load_history", load_history)
    graph.add_node("classify_question", classify_question)
    graph.add_node("resolve_follow_up", resolve_follow_up)
    graph.add_node("retrieve_metadata", retrieve_metadata)
    graph.add_node("run_metadata_tools", run_metadata_tools)
    graph.add_node("retrieve_chunks", retrieve_chunks)
    graph.set_entry_point("load_history")
    graph.add_edge("load_history", "classify_question")
    graph.add_conditional_edges(
        "classify_question",
        _after_classification,
        {"resolve_follow_up": "resolve_follow_up", "retrieve_metadata": "retrieve_metadata"},
    )
    graph.add_edge("resolve_follow_up", "retrieve_metadata")
    graph.add_conditional_edges(
        "retrieve_metadata",
        _after_metadata,
        {"run_metadata_tools": "run_metadata_tools", "retrieve_chunks": "retrieve_chunks"},
    )
    graph.add_conditional_edges(
        "run_metadata_tools",
        _after_metadata_tools,
        {"retrieve_chunks": "retrieve_chunks", "end": END},
    )
    graph.add_edge("retrieve_chunks", END)
    return graph.compile()


_graph = build_graph()


def run_retrieval_graph(session_id: str, query: str) -> CreatorSessionState:
    return _graph.invoke({"session_id": session_id, "query": query})
