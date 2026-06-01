import argparse
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

ASSIGNMENT_EVALS = [
    {
        "id": "engagement_rates",
        "question": "What is the engagement rate of each video?",
        "required_metadata_videos": {"A", "B"},
        "forbid_chunks": True,
        "required_citation_tags": {"[Video A metadata]", "[Video B metadata]"},
        "required_engagement_videos": {"A", "B"},
    },
    {
        "id": "creator_b_followers",
        "question": "Who is the creator of Video B and what is their follower count?",
        "required_metadata_videos": {"B"},
        "forbid_chunks": True,
        "required_citation_tags": {"[Video B metadata]"},
        "required_creator_video": "B",
        "required_follower_video": "B",
    },
    {
        "id": "first_five_second_hooks",
        "question": "Compare the hooks in the first 5 seconds.",
        "required_metadata_videos": {"A", "B"},
        "require_chunks": True,
        "require_hook_chunks": True,
    },
    {
        "id": "why_a_more_engagement",
        "question": "Why did Video A get more engagement than Video B?",
        "required_metadata_videos": {"A", "B"},
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
        "required_citation_tags": {"[Video A metadata]", "[Video B metadata]"},
    },
    {
        "id": "improve_b_from_a",
        "question": "Suggest improvements for B based on what worked in A.",
        "required_metadata_videos": {"A", "B"},
        "required_chunk_videos": {"A", "B"},
        "require_chunks": True,
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


def _request_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_chat(api_base: str, session_id: str, question: str) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    body = json.dumps({"session_id": session_id, "message": question}).encode("utf-8")
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/chat",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        raw = response.read().decode("utf-8")

    answer = ""
    sources: list[dict[str, Any]] = []
    events = parse_sse(raw)
    for event in events:
        event_name = event.get("event")
        payload = event.get("data") or {}
        if event_name == "sources":
            sources = payload.get("sources", [])
        elif event_name == "token":
            answer += payload.get("token", "")
        elif event_name == "error":
            raise RuntimeError(payload.get("message", "Chat stream returned an error event"))
    return answer, sources, events


def parse_sse(raw: str) -> list[dict[str, Any]]:
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
            payload = json.loads("\n".join(data_lines))
        events.append({"event": event_name, "data": payload})
    return events


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


def _streamed_successfully(events: list[dict[str, Any]] | None) -> bool:
    if events is None:
        return True
    if any(event.get("event") == "error" for event in events):
        return False
    return any(event.get("event") == "done" and (event.get("data") or {}).get("ok") is True for event in events)


def validate_eval_case(
    case: dict[str, Any],
    answer: str,
    sources: list[dict[str, Any]],
    status_metadata: dict[str, dict[str, Any]] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> list[str]:
    failures: list[str] = []
    status_metadata = status_metadata or {}
    metadata_sources = [source for source in sources if source.get("type") == "metadata"]
    chunk_sources = [source for source in sources if source.get("type") == "chunk"]
    metadata_videos = {source.get("video_id") for source in metadata_sources}
    chunk_videos = {source.get("video_id") for source in chunk_sources}

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

    for tag in case.get("required_citation_tags", set()):
        if tag not in answer:
            failures.append(f"answer did not cite {tag}")

    if not CITATION_PATTERN.search(answer):
        failures.append("answer contains no source citation")

    source_tags = {source.get("source_tag") for source in sources if source.get("source_tag")}
    if source_tags and not any(tag in answer for tag in source_tags):
        failures.append("answer did not include any returned source tag")

    if not answer.strip():
        failures.append("answer was empty")

    for video_id in case.get("required_engagement_videos", set()):
        video = status_metadata.get(video_id)
        if not video:
            failures.append(f"missing Postgres metadata for Video {video_id}")
            continue
        expected_rate = video.get("engagement_rate")
        if not _answer_contains_number(answer, expected_rate):
            failures.append(f"engagement rate for Video {video_id} does not match Postgres value {expected_rate}")

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
        if _missing_count(follower_count):
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
        answer, sources, events = _post_chat(api_base, session_id, case["question"])
        streamed_successfully = _streamed_successfully(events)
        failures = validate_eval_case(case, answer, sources, status_metadata=status_metadata, events=events)
        results.append(
            EvalResult(
                id=case["id"],
                question=case["question"],
                ok=not failures,
                failures=failures,
                answer=answer,
                sources=sources,
                streamed_successfully=streamed_successfully,
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
    except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:
        print(f"Eval run failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        _print_text_report(results)

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
