import argparse
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

CITATION_PATTERN = re.compile(r"\[Video [AB](?: metadata|, chunk \d+, \d+:\d\d-\d+:\d\d)\]")
FOLLOWER_COUNT_PATTERN = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*followers?\b", re.IGNORECASE)
INVALID_CITATION_PATTERNS = [
    re.compile(r"\[source_tag:", re.IGNORECASE),
    re.compile(r"\[citation:", re.IGNORECASE),
    re.compile(r"\[POSTGRES METADATA TOOL RESULTS\]", re.IGNORECASE),
]
METADATA_ONLY = "METADATA_ONLY"
TRANSCRIPT_ONLY = "TRANSCRIPT_ONLY"
HOOK_COMPARISON = "HOOK_COMPARISON"
MIXED_COMPARISON = "MIXED_COMPARISON"
IMPROVEMENT_SUGGESTION = "IMPROVEMENT_SUGGESTION"
HOOK_RETRIEVAL = "hook_retrieval"
COMPARISON_RETRIEVAL = "comparison_retrieval"
METADATA_AUGMENTED_RETRIEVAL = "metadata_augmented_retrieval"
UNAVAILABLE_TERMS = ("unavailable", "not available", "not provided", "missing", "unknown", "not recorded")
CHAT_REQUEST_EXCEPTIONS = (
    urllib.error.URLError,
    RuntimeError,
    TimeoutError,
    http.client.IncompleteRead,
    json.JSONDecodeError,
)

ASSIGNMENT_EVALS = [
    {
        "id": "engagement_rates",
        "question": "What is the engagement rate of each video?",
        "expected_route": METADATA_ONLY,
        "expected_retrieval_policy": None,
        "required_metadata_videos": {"A", "B"},
        "forbid_chunks": True,
        "required_citation_tags": {"[Video A metadata]", "[Video B metadata]"},
        "required_engagement_videos": {"A", "B"},
    },
    {
        "id": "creator_b_followers",
        "question": "Who is the creator of Video B and what is their follower count?",
        "expected_route": METADATA_ONLY,
        "expected_retrieval_policy": None,
        "required_metadata_videos": {"B"},
        "forbid_chunks": True,
        "required_citation_tags": {"[Video B metadata]"},
        "required_creator_video": "B",
        "required_follower_video": "B",
    },
    {
        "id": "first_five_second_hooks",
        "question": "Compare the hooks in the first 5 seconds.",
        "expected_route": HOOK_COMPARISON,
        "expected_retrieval_policy": HOOK_RETRIEVAL,
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
        "require_hook_chunks": True,
        "answer_citations_hook_chunks_only": True,
        "required_answer_chunk_videos": {"A", "B"},
    },
    {
        "id": "why_a_more_engagement",
        "question": "Why did Video A get more engagement than Video B?",
        "expected_route": MIXED_COMPARISON,
        "expected_retrieval_policy": METADATA_AUGMENTED_RETRIEVAL,
        "required_metadata_videos": {"A", "B"},
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
        "required_citation_tags": {"[Video A metadata]", "[Video B metadata]"},
        "required_engagement_videos": {"A", "B"},
        "required_view_videos": {"A", "B"},
        "required_answer_chunk_videos": {"A", "B"},
    },
    {
        "id": "improve_b_from_a",
        "question": "Suggest improvements for B based on what worked in A.",
        "expected_route": IMPROVEMENT_SUGGESTION,
        "expected_retrieval_policy": METADATA_AUGMENTED_RETRIEVAL,
        "required_metadata_videos": {"A", "B"},
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
        "required_answer_chunk_videos": {"A", "B"},
    },
    {
        "id": "stats_scorecard",
        "question": (
            "Build a compact stats scorecard for both videos: views, likes, comments, "
            "engagement rate, and follower count."
        ),
        "expected_route": METADATA_ONLY,
        "expected_retrieval_policy": None,
        "required_metadata_videos": {"A", "B"},
        "forbid_chunks": True,
        "required_citation_tags": {"[Video A metadata]", "[Video B metadata]"},
        "required_numeric_fields": {
            "A": {"views", "likes", "comments", "engagement_rate", "creator_followers"},
            "B": {"views", "likes", "comments", "engagement_rate", "creator_followers"},
        },
    },
    {
        "id": "missing_shares_wrong_metric",
        "question": "How many shares did Video A get?",
        "expected_route": METADATA_ONLY,
        "expected_retrieval_policy": None,
        "required_metadata_videos": {"A"},
        "forbid_chunks": True,
        "required_citation_tags": {"[Video A metadata]"},
        "required_unavailable_terms": {"share"},
    },
    {
        "id": "vague_watchability",
        "question": "Which one feels more watchable, and why?",
        "expected_route": TRANSCRIPT_ONLY,
        "expected_retrieval_policy": COMPARISON_RETRIEVAL,
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
        "required_answer_chunk_videos": {"A", "B"},
    },
    {
        "id": "creative_taglines",
        "question": "Give each video a punchy tagline based only on what is said.",
        "expected_route": TRANSCRIPT_ONLY,
        "expected_retrieval_policy": COMPARISON_RETRIEVAL,
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
        "required_answer_chunk_videos": {"A", "B"},
    },
    {
        "id": "multi_level_hook_metrics_improve",
        "question": (
            "First compare the opening hooks, then recommend two changes for Video B using "
            "A's strongest moment and the performance data."
        ),
        "expected_route": IMPROVEMENT_SUGGESTION,
        "expected_retrieval_policy": METADATA_AUGMENTED_RETRIEVAL,
        "required_metadata_videos": {"A", "B"},
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
        "required_answer_chunk_videos": {"A", "B"},
        "required_citation_tags": {"[Video A metadata]", "[Video B metadata]"},
    },
    {
        "id": "open_ended_next_post",
        "question": "If I only have time to remake one of these, what should I change first?",
        "expected_route": IMPROVEMENT_SUGGESTION,
        "expected_retrieval_policy": METADATA_AUGMENTED_RETRIEVAL,
        "required_metadata_videos": {"A", "B"},
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
        "required_answer_chunk_videos": {"A", "B"},
    },
    {
        "id": "incorrect_engagement_winner",
        "question": "Video B clearly won on engagement, right?",
        "expected_route": METADATA_ONLY,
        "expected_retrieval_policy": None,
        "required_metadata_videos": {"A", "B"},
        "forbid_chunks": True,
        "required_citation_tags": {"[Video A metadata]", "[Video B metadata]"},
        "required_engagement_videos": {"A", "B"},
    },
]


@dataclass
class EvalResult:
    id: str
    question: str
    ok: bool
    failures: list[str]
    answer: str
    sources: list[dict[str, Any]]
    streamed_successfully: bool
    route: str | None = None
    retrieval_policy: str | None = None
    transport_error: str | None = None


@dataclass
class ChatEvalResponse:
    answer: str
    sources: list[dict[str, Any]]
    events: list[dict[str, Any]]
    route: str | None
    retrieval_policy: str | None
    transport_error: str | None = None


def _request_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _read_response_body(response: Any) -> tuple[str, str | None]:
    try:
        return response.read().decode("utf-8"), None
    except http.client.IncompleteRead as exc:
        partial = exc.partial or b""
        raw = partial.decode("utf-8", errors="replace")
        return raw, f"chat stream ended before a complete HTTP chunk was received: {exc}"


def _post_chat(api_base: str, session_id: str, question: str) -> ChatEvalResponse:
    body = json.dumps({"session_id": session_id, "message": question}).encode("utf-8")
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/chat",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        raw, transport_error = _read_response_body(response)

    answer = ""
    sources: list[dict[str, Any]] = []
    events = parse_sse(raw, skip_invalid=transport_error is not None)
    route, retrieval_policy = _route_trace_from_events(events)
    stream_error = None
    for event in events:
        event_name = event.get("event")
        payload = event.get("data") or {}
        if event_name == "sources":
            sources = payload.get("sources", [])
        elif event_name == "token":
            answer += payload.get("token", "")
        elif event_name == "error":
            stream_error = payload.get("message", "Chat stream returned an error event")
    if stream_error:
        error_message = f"chat stream returned an error event: {stream_error}"
        transport_error = f"{transport_error}; {error_message}" if transport_error else error_message
    return ChatEvalResponse(
        answer=answer,
        sources=sources,
        events=events,
        route=route,
        retrieval_policy=retrieval_policy,
        transport_error=transport_error,
    )


def parse_sse(raw: str, *, skip_invalid: bool = False) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        event_name = "message"
        data_lines = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        payload: dict[str, Any] = {}
        if data_lines:
            try:
                payload = json.loads("\n".join(data_lines))
            except json.JSONDecodeError:
                if skip_invalid:
                    continue
                raise
        events.append({"event": event_name, "data": payload})
    return events


def _route_trace_from_events(events: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    route = None
    retrieval_policy = None
    for event in events:
        if event.get("event") not in {"sources", "done"}:
            continue
        payload = event.get("data") or {}
        route = payload.get("route") or route
        if "retrieval_policy" in payload:
            retrieval_policy = payload.get("retrieval_policy")
    return route, retrieval_policy


def _metadata_by_video(status: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(video.get("video_id")): video for video in status.get("metadata", []) if video.get("video_id")}


def _number_variants(value: object) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return set()
        try:
            number = float(stripped.replace(",", ""))
        except ValueError:
            return {stripped}
    else:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return {str(value)}

    variants = {str(value), f"{number:.4f}".rstrip("0").rstrip("."), f"{number:.2f}"}
    if number.is_integer():
        integer = int(number)
        variants.update({str(integer), f"{integer:,}"})
    return {variant for variant in variants if variant}


def _answer_contains_number(answer: str, value: object) -> bool:
    answer_without_commas = answer.replace(",", "")
    for variant in _number_variants(value):
        normalized_variant = variant.replace(",", "")
        if not normalized_variant:
            continue
        if re.search(rf"(?<![\d.]){re.escape(normalized_variant)}%?(?![\d.])", answer_without_commas):
            return True
    return False


def _missing_count(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "0", "unknown", "unavailable", "none", "null"}
    return value == 0


def _metric_available(video: dict[str, Any], available_key: str, value_key: str) -> bool:
    if available_key in video:
        return bool(video.get(available_key))
    return not _missing_count(video.get(value_key))


def _unavailable_stated(answer: str) -> bool:
    lowered = answer.lower()
    return any(term in lowered for term in UNAVAILABLE_TERMS)


def _streamed_successfully(events: list[dict[str, Any]] | None) -> bool:
    if events is None:
        return True
    if any(event.get("event") == "error" for event in events):
        return False
    return any(event.get("event") == "done" and (event.get("data") or {}).get("ok") is True for event in events)


def _video_window(answer: str, video_id: str) -> str:
    match = re.search(rf"video\s+{video_id}\b(.{{0,120}})", answer, re.IGNORECASE | re.DOTALL)
    return match.group(0) if match else ""


def validate_eval_case(
    case: dict[str, Any],
    answer: str,
    sources: list[dict[str, Any]],
    status_metadata: dict[str, dict[str, Any]] | None = None,
    events: list[dict[str, Any]] | None = None,
    route: str | None = None,
    retrieval_policy: str | None = None,
    enforce_route: bool = False,
) -> list[str]:
    failures: list[str] = []
    status_metadata = status_metadata or {}
    metadata_sources = [source for source in sources if source.get("type") == "metadata"]
    chunk_sources = [source for source in sources if source.get("type") == "chunk"]
    metadata_videos = {source.get("video_id") for source in metadata_sources}
    chunk_videos = {source.get("video_id") for source in chunk_sources}

    if enforce_route:
        expected_route = case.get("expected_route")
        if expected_route and route != expected_route:
            failures.append(f"expected route {expected_route} but got {route or 'unavailable'}")
        if "expected_retrieval_policy" in case:
            expected_policy = case.get("expected_retrieval_policy")
            if retrieval_policy != expected_policy:
                failures.append(
                    f"expected retrieval policy {expected_policy or 'none'} but got {retrieval_policy or 'none'}"
                )

    if not _streamed_successfully(events):
        failures.append("response did not stream to a successful done event")

    for video_id in case.get("required_metadata_videos", set()):
        if video_id not in metadata_videos:
            failures.append(f"missing metadata source for Video {video_id}")

    for video_id in case.get("required_chunk_videos", set()):
        if video_id not in chunk_videos:
            failures.append(f"missing transcript chunk source for Video {video_id}")

    if case.get("forbid_chunks") and chunk_sources:
        failures.append("metadata-only question returned transcript chunk sources")

    if case.get("require_chunks") and not chunk_sources:
        failures.append("expected transcript chunk sources but none were returned")
    if case.get("require_chunks") and chunk_sources:
        chunk_tags = {source.get("source_tag") for source in chunk_sources if source.get("source_tag")}
        if chunk_tags and not any(tag in answer for tag in chunk_tags):
            failures.append("answer did not cite any returned transcript chunk source")

    if case.get("require_hook_chunks"):
        non_hook_sources = [source for source in chunk_sources if float(source.get("start_time") or 0.0) >= 5.0]
        if non_hook_sources:
            failures.append("hook eval returned chunk sources starting at or after 5 seconds")
    if case.get("answer_citations_hook_chunks_only"):
        answer_citations = CITATION_PATTERN.findall(answer)
        metadata_citations = [citation for citation in answer_citations if citation.endswith(" metadata]")]
        if metadata_citations:
            failures.append("hook answer cited metadata instead of hook chunks only")
        non_hook_answer_tags = {
            source.get("source_tag")
            for source in chunk_sources
            if float(source.get("start_time") or 0.0) >= 5.0 and source.get("source_tag") in answer
        }
        if non_hook_answer_tags:
            failures.append("hook answer cited a non-hook transcript chunk")

    for tag in case.get("required_citation_tags", set()):
        if tag not in answer:
            failures.append(f"answer did not cite {tag}")

    if not CITATION_PATTERN.search(answer):
        failures.append("answer contains no source citation")
    if any(pattern.search(answer) for pattern in INVALID_CITATION_PATTERNS):
        failures.append("answer contains an invalid citation wrapper or non-source citation")

    source_tags = {source.get("source_tag") for source in sources if source.get("source_tag")}
    if source_tags and not any(tag in answer for tag in source_tags):
        failures.append("answer did not include any returned source tag")

    for video_id in case.get("required_answer_chunk_videos", set()):
        video_chunk_tags = {
            source.get("source_tag")
            for source in chunk_sources
            if source.get("video_id") == video_id and source.get("source_tag")
        }
        if video_chunk_tags and not any(tag in answer for tag in video_chunk_tags):
            failures.append(f"answer did not cite a returned Video {video_id} transcript chunk")

    for video_id in case.get("required_answer_source_videos", set()):
        video_source_tags = {
            source.get("source_tag")
            for source in sources
            if source.get("video_id") == video_id and source.get("source_tag")
        }
        if video_source_tags and not any(tag in answer for tag in video_source_tags):
            failures.append(f"answer did not cite a returned Video {video_id} source")

    if not answer.strip():
        failures.append("answer was empty")

    for video_id, fields in case.get("required_numeric_fields", {}).items():
        video = status_metadata.get(video_id)
        if not video:
            failures.append(f"missing Postgres metadata for Video {video_id}")
            continue
        for field_name in fields:
            available_key = f"{field_name}_available"
            expected_value = video.get(field_name)
            if not _metric_available(video, available_key, field_name):
                if not _unavailable_stated(answer):
                    failures.append(f"{field_name} for Video {video_id} is unavailable but answer did not say so")
            elif not _answer_contains_number(answer, expected_value):
                failures.append(f"{field_name} for Video {video_id} does not match Postgres value {expected_value}")

    for term in case.get("required_unavailable_terms", set()):
        if term.lower() not in answer.lower():
            failures.append(f"answer did not mention unavailable field {term}")
        if not _unavailable_stated(answer):
            failures.append(f"{term} is unavailable but answer did not say so")

    for video_id in case.get("required_engagement_videos", set()):
        video = status_metadata.get(video_id)
        if not video:
            failures.append(f"missing Postgres metadata for Video {video_id}")
            continue
        expected_rate = video.get("engagement_rate")
        if not _metric_available(video, "engagement_rate_available", "engagement_rate"):
            if "unavailable" not in answer.lower():
                failures.append(f"engagement rate for Video {video_id} is unavailable but answer did not say so")
            if re.search(r"\b0(?:\.0+)?\s*%", _video_window(answer, video_id)):
                failures.append(
                    f"engagement rate for Video {video_id} is unavailable but answer appears to treat it as 0%"
                )
        elif not _answer_contains_number(answer, expected_rate):
            failures.append(f"engagement rate for Video {video_id} does not match Postgres value {expected_rate}")

    for video_id in case.get("required_view_videos", set()):
        video = status_metadata.get(video_id)
        if not video:
            failures.append(f"missing Postgres metadata for Video {video_id}")
            continue
        if not _metric_available(video, "views_available", "views"):
            if "unavailable" not in answer.lower():
                failures.append(f"views for Video {video_id} are unavailable but answer did not say so")
            if re.search(r"\b0\s+views?\b", _video_window(answer, video_id), re.IGNORECASE):
                failures.append(f"views for Video {video_id} are unavailable but answer appears to treat them as 0")

    creator_video_id = case.get("required_creator_video")
    if creator_video_id:
        video = status_metadata.get(creator_video_id)
        creator = (video or {}).get("creator") or "unknown"
        if creator == "unknown":
            if "unknown" not in answer.lower() and "unavailable" not in answer.lower():
                failures.append(f"creator for Video {creator_video_id} is unknown but answer did not say so")
        elif creator.lower() not in answer.lower():
            failures.append(f"creator for Video {creator_video_id} does not match Postgres value {creator}")

    follower_video_id = case.get("required_follower_video")
    if follower_video_id:
        video = status_metadata.get(follower_video_id)
        follower_count = (video or {}).get("creator_followers")
        if not video or not _metric_available(video, "creator_followers_available", "creator_followers"):
            if "unavailable" not in answer.lower():
                failures.append(
                    f"follower count for Video {follower_video_id} is missing but answer did not say unavailable"
                )
            if FOLLOWER_COUNT_PATTERN.search(answer):
                failures.append(
                    f"follower count for Video {follower_video_id} is missing but answer appears to invent a number"
                )
        elif not _answer_contains_number(answer, follower_count):
            failures.append(
                f"follower count for Video {follower_video_id} does not match Postgres value {follower_count}"
            )

    return failures


def run_assignment_evals(api_base: str, session_id: str) -> list[EvalResult]:
    status = _request_json(f"{api_base.rstrip('/')}/status/{session_id}")
    if status.get("status") not in {"ready", "completed"}:
        raise RuntimeError(f"Session {session_id} is {status.get('status')}, not completed")
    status_metadata = _metadata_by_video(status)

    results = []
    for case in ASSIGNMENT_EVALS:
        try:
            chat_response = _post_chat(api_base, session_id, case["question"])
        except CHAT_REQUEST_EXCEPTIONS as exc:
            results.append(
                EvalResult(
                    id=case["id"],
                    question=case["question"],
                    ok=False,
                    failures=[f"chat request failed: {exc}"],
                    answer="",
                    sources=[],
                    streamed_successfully=False,
                    transport_error=str(exc),
                )
            )
            continue
        answer = chat_response.answer
        sources = chat_response.sources
        events = chat_response.events
        route = chat_response.route
        retrieval_policy = chat_response.retrieval_policy
        streamed_successfully = _streamed_successfully(events)
        if chat_response.transport_error:
            failures = [chat_response.transport_error]
            if not streamed_successfully:
                failures.append("response did not stream to a successful done event")
        else:
            failures = validate_eval_case(
                case,
                answer,
                sources,
                status_metadata=status_metadata,
                events=events,
                route=route,
                retrieval_policy=retrieval_policy,
                enforce_route=True,
            )
        results.append(
            EvalResult(
                id=case["id"],
                question=case["question"],
                ok=not failures,
                failures=failures,
                answer=answer,
                sources=sources,
                streamed_successfully=streamed_successfully,
                route=route,
                retrieval_policy=retrieval_policy,
                transport_error=chat_response.transport_error,
            )
        )
    return results


def _print_text_report(results: list[EvalResult]) -> None:
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"[{status}] {result.id}: {result.question}")
        if result.failures:
            for failure in result.failures:
                print(f"  - {failure}")
        source_tags = [source.get("source_tag") for source in result.sources if source.get("source_tag")]
        print(f"  streamed: {result.streamed_successfully}")
        print(f"  route: {result.route or 'unavailable'}")
        print(f"  retrieval_policy: {result.retrieval_policy or 'none'}")
        print(f"  sources: {', '.join(source_tags) if source_tags else 'none'}")
        print(f"  answer: {result.answer[:240].strip()}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run assignment question evals against a completed session.")
    parser.add_argument("--session-id", default=os.getenv("SESSION_ID"), help="Completed session ID to evaluate.")
    parser.add_argument(
        "--api-base",
        default=os.getenv("EVAL_API_BASE") or os.getenv("NEXT_PUBLIC_API_BASE") or "http://127.0.0.1:8000",
        help="Backend API base URL.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON results.")
    args = parser.parse_args(argv)

    if not args.session_id:
        parser.error("--session-id is required, or set SESSION_ID")

    try:
        results = run_assignment_evals(api_base=args.api_base, session_id=args.session_id)
    except CHAT_REQUEST_EXCEPTIONS as exc:
        print(f"Eval run failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        _print_text_report(results)

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
