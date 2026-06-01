import http.client
import unittest
from unittest.mock import patch

from backend.evals.assignment_eval import (
    ASSIGNMENT_EVALS,
    COMPARISON_RETRIEVAL,
    HOOK_RETRIEVAL,
    METADATA_AUGMENTED_RETRIEVAL,
    METADATA_ONLY,
    MIXED_COMPARISON,
    TRANSCRIPT_ONLY,
    ChatEvalResponse,
    _read_response_body,
    parse_sse,
    run_assignment_evals,
    validate_eval_case,
)


class AssignmentEvalTests(unittest.TestCase):
    def test_parse_sse_collects_named_events(self) -> None:
        raw = (
            'event: sources\ndata: {"sources": [{"type": "metadata", "video_id": "A"}]}\n\n'
            'event: token\ndata: {"token": "hello"}\n\n'
            'event: done\ndata: {"ok": true}\n\n'
        )

        events = parse_sse(raw)

        self.assertEqual([event["event"] for event in events], ["sources", "token", "done"])
        self.assertEqual(events[0]["data"]["sources"][0]["video_id"], "A")

    def test_parse_sse_can_skip_invalid_partial_event(self) -> None:
        raw = 'event: token\ndata: {"token": "ok"}\n\nevent: token\ndata: {"token":'

        events = parse_sse(raw, skip_invalid=True)

        self.assertEqual(events, [{"event": "token", "data": {"token": "ok"}}])

    def test_incomplete_chunk_read_returns_partial_body_and_error(self) -> None:
        class BrokenResponse:
            def read(self) -> bytes:
                raise http.client.IncompleteRead(b'event: token\ndata: {"token": "partial"}\n\n')

        raw, error = _read_response_body(BrokenResponse())

        self.assertEqual(raw, 'event: token\ndata: {"token": "partial"}\n\n')
        self.assertIn("chat stream ended before a complete HTTP chunk was received", error or "")

    def test_run_assignment_evals_converts_chat_transport_errors_to_failures(self) -> None:
        status = {"status": "completed", "metadata": []}

        with (
            patch("backend.evals.assignment_eval._request_json", return_value=status),
            patch("backend.evals.assignment_eval._post_chat", side_effect=http.client.IncompleteRead(b"")),
        ):
            results = run_assignment_evals("http://example.test", "session-1")

        self.assertEqual(len(results), len(ASSIGNMENT_EVALS))
        self.assertFalse(results[0].ok)
        self.assertFalse(results[0].streamed_successfully)
        self.assertIn("chat request failed", results[0].failures[0])

    def test_run_assignment_evals_keeps_stream_error_failures_focused(self) -> None:
        status = {"status": "completed", "metadata": []}
        chat_response = ChatEvalResponse(
            answer="",
            sources=[],
            events=[],
            route=None,
            retrieval_policy=None,
            transport_error="chat stream returned an error event: qdrant down",
        )

        with (
            patch("backend.evals.assignment_eval._request_json", return_value=status),
            patch("backend.evals.assignment_eval._post_chat", return_value=chat_response),
        ):
            results = run_assignment_evals("http://example.test", "session-1")

        self.assertEqual(
            results[0].failures,
            [
                "chat stream returned an error event: qdrant down",
                "response did not stream to a successful done event",
            ],
        )

    def test_metadata_only_eval_rejects_chunk_sources(self) -> None:
        case = ASSIGNMENT_EVALS[0]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
            {"type": "chunk", "video_id": "A", "source_tag": "[Video A, chunk 0, 00:00-00:04]"},
        ]

        failures = validate_eval_case(case, "A [Video A metadata], B [Video B metadata]", sources)

        self.assertIn("metadata-only question returned transcript chunk sources", failures)

    def test_engagement_eval_checks_postgres_values(self) -> None:
        case = ASSIGNMENT_EVALS[0]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
        ]
        metadata = {
            "A": {"engagement_rate": 1.25},
            "B": {"engagement_rate": 0.75},
        }

        failures = validate_eval_case(
            case,
            "Video A is 1.25% [Video A metadata]. Video B is 0.50% [Video B metadata].",
            sources,
            status_metadata=metadata,
            events=[{"event": "done", "data": {"ok": True}}],
        )

        self.assertIn("engagement rate for Video B does not match Postgres value 0.75", failures)

    def test_extended_eval_cases_cover_requested_question_types(self) -> None:
        expected_ids = {
            "stats_scorecard",
            "missing_shares_wrong_metric",
            "vague_watchability",
            "creative_taglines",
            "multi_level_hook_metrics_improve",
            "open_ended_next_post",
            "incorrect_engagement_winner",
        }

        self.assertTrue(expected_ids.issubset({case["id"] for case in ASSIGNMENT_EVALS}))

    def test_eval_rejects_wrong_route_when_route_enforced(self) -> None:
        case = ASSIGNMENT_EVALS[0]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
        ]
        metadata = {
            "A": {"engagement_rate": 1.25, "engagement_rate_available": True},
            "B": {"engagement_rate": 0.75, "engagement_rate_available": True},
        }

        failures = validate_eval_case(
            case,
            "Video A is 1.25% [Video A metadata]. Video B is 0.75% [Video B metadata].",
            sources,
            status_metadata=metadata,
            events=[{"event": "done", "data": {"ok": True}}],
            route=MIXED_COMPARISON,
            retrieval_policy=METADATA_AUGMENTED_RETRIEVAL,
            enforce_route=True,
        )

        self.assertIn("expected route METADATA_ONLY but got MIXED_COMPARISON", failures)
        self.assertIn(
            "expected retrieval policy none but got metadata_augmented_retrieval",
            failures,
        )

    def test_eval_accepts_expected_metadata_route_when_route_enforced(self) -> None:
        case = ASSIGNMENT_EVALS[0]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
        ]
        metadata = {
            "A": {"engagement_rate": 1.25, "engagement_rate_available": True},
            "B": {"engagement_rate": 0.75, "engagement_rate_available": True},
        }

        failures = validate_eval_case(
            case,
            "Video A is 1.25% [Video A metadata]. Video B is 0.75% [Video B metadata].",
            sources,
            status_metadata=metadata,
            events=[{"event": "done", "data": {"ok": True}}],
            route=METADATA_ONLY,
            retrieval_policy=None,
            enforce_route=True,
        )

        self.assertEqual(failures, [])

    def test_unavailable_engagement_must_be_stated_as_unavailable(self) -> None:
        case = ASSIGNMENT_EVALS[0]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
        ]
        metadata = {
            "A": {"engagement_rate": 1.25, "engagement_rate_available": True},
            "B": {"engagement_rate": 0.0, "engagement_rate_available": False},
        }

        failures = validate_eval_case(
            case,
            "Video A is 1.25% [Video A metadata]. Video B is 0% [Video B metadata].",
            sources,
            status_metadata=metadata,
            events=[{"event": "done", "data": {"ok": True}}],
        )

        self.assertIn("engagement rate for Video B is unavailable but answer did not say so", failures)

    def test_unavailable_views_must_not_be_treated_as_zero(self) -> None:
        case = ASSIGNMENT_EVALS[3]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
            {
                "type": "chunk",
                "video_id": "A",
                "start_time": 0.0,
                "source_tag": "[Video A, chunk 0, 00:00-00:04]",
            },
            {
                "type": "chunk",
                "video_id": "B",
                "start_time": 0.0,
                "source_tag": "[Video B, chunk 0, 00:00-00:04]",
            },
        ]
        metadata = {
            "A": {"engagement_rate": 1.25, "engagement_rate_available": True, "views": 1000, "views_available": True},
            "B": {"engagement_rate": 0.0, "engagement_rate_available": False, "views": 0, "views_available": False},
        }

        failures = validate_eval_case(
            case,
            (
                "Video A got more because it had 1000 views [Video A metadata] and "
                "Video B had 0 views [Video B metadata]. "
                "A hook [Video A, chunk 0, 00:00-00:04], B hook [Video B, chunk 0, 00:00-00:04]."
            ),
            sources,
            status_metadata=metadata,
            events=[{"event": "done", "data": {"ok": True}}],
        )

        self.assertIn("views for Video B are unavailable but answer did not say so", failures)
        self.assertIn("views for Video B are unavailable but answer appears to treat them as 0", failures)

    def test_missing_follower_count_must_be_unavailable(self) -> None:
        case = ASSIGNMENT_EVALS[1]
        sources = [{"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"}]
        metadata = {"B": {"creator": "demo_creator", "creator_followers": 0}}

        failures = validate_eval_case(
            case,
            "Video B is by demo_creator with 10,000 followers [Video B metadata].",
            sources,
            status_metadata=metadata,
            events=[{"event": "done", "data": {"ok": True}}],
        )

        self.assertIn("follower count for Video B is missing but answer did not say unavailable", failures)
        self.assertIn("follower count for Video B is missing but answer appears to invent a number", failures)

    def test_stats_scorecard_checks_multiple_postgres_values(self) -> None:
        case = next(item for item in ASSIGNMENT_EVALS if item["id"] == "stats_scorecard")
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
        ]
        metadata = {
            "A": {
                "views": 1000,
                "views_available": True,
                "likes": 120,
                "likes_available": True,
                "comments": 12,
                "comments_available": True,
                "engagement_rate": 13.2,
                "engagement_rate_available": True,
                "creator_followers": 900,
                "creator_followers_available": True,
            },
            "B": {
                "views": 2000,
                "views_available": True,
                "likes": 80,
                "likes_available": True,
                "comments": 8,
                "comments_available": True,
                "engagement_rate": 4.4,
                "engagement_rate_available": True,
                "creator_followers": 0,
                "creator_followers_available": False,
            },
        }

        failures = validate_eval_case(
            case,
            (
                "A: 1000 views, 120 likes, 12 comments, 13.2%, 900 followers [Video A metadata]. "
                "B: 2000 views, 80 likes, 99 comments, 4.4%, followers unavailable [Video B metadata]."
            ),
            sources,
            status_metadata=metadata,
            events=[{"event": "done", "data": {"ok": True}}],
            route=METADATA_ONLY,
            retrieval_policy=None,
            enforce_route=True,
        )

        self.assertIn("comments for Video B does not match Postgres value 8", failures)

    def test_missing_share_eval_requires_unavailable_language(self) -> None:
        case = next(item for item in ASSIGNMENT_EVALS if item["id"] == "missing_shares_wrong_metric")
        sources = [{"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"}]

        failures = validate_eval_case(
            case,
            "Video A had 100 shares [Video A metadata].",
            sources,
            events=[{"event": "done", "data": {"ok": True}}],
            route=METADATA_ONLY,
            retrieval_policy=None,
            enforce_route=True,
        )

        self.assertIn("share is unavailable but answer did not say so", failures)

    def test_vague_eval_requires_transcript_route_and_balanced_policy(self) -> None:
        case = next(item for item in ASSIGNMENT_EVALS if item["id"] == "vague_watchability")
        sources = [
            {
                "type": "chunk",
                "video_id": "A",
                "start_time": 30.0,
                "source_tag": "[Video A, chunk 2, 00:30-00:44]",
            },
            {
                "type": "chunk",
                "video_id": "B",
                "start_time": 10.0,
                "source_tag": "[Video B, chunk 1, 00:10-00:20]",
            },
        ]

        failures = validate_eval_case(
            case,
            "A feels more watchable [Video A, chunk 2, 00:30-00:44]. B is less direct [Video B, chunk 1, 00:10-00:20].",
            sources,
            events=[{"event": "done", "data": {"ok": True}}],
            route=TRANSCRIPT_ONLY,
            retrieval_policy=COMPARISON_RETRIEVAL,
            enforce_route=True,
        )

        self.assertEqual(failures, [])

    def test_requires_successful_done_event_when_events_are_provided(self) -> None:
        case = ASSIGNMENT_EVALS[1]
        sources = [{"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"}]
        metadata = {"B": {"creator": "demo_creator", "creator_followers": 123}}

        failures = validate_eval_case(
            case,
            "Video B is by demo_creator with 123 followers [Video B metadata].",
            sources,
            status_metadata=metadata,
            events=[{"event": "token", "data": {"token": "partial"}}],
        )

        self.assertIn("response did not stream to a successful done event", failures)

    def test_rejects_invalid_citation_wrappers(self) -> None:
        case = ASSIGNMENT_EVALS[1]
        sources = [{"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"}]
        metadata = {"B": {"creator": "demo_creator", "creator_followers": 123}}

        failures = validate_eval_case(
            case,
            "Video B is by demo_creator with 123 followers [source_tag: [Video B metadata]].",
            sources,
            status_metadata=metadata,
            events=[{"event": "done", "data": {"ok": True}}],
        )

        self.assertIn("answer contains an invalid citation wrapper or non-source citation", failures)

    def test_hook_eval_rejects_non_hook_chunks(self) -> None:
        case = ASSIGNMENT_EVALS[2]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
            {
                "type": "chunk",
                "video_id": "A",
                "start_time": 10.0,
                "source_tag": "[Video A, chunk 3, 00:10-00:14]",
            },
        ]

        failures = validate_eval_case(case, "Hook answer [Video A, chunk 3, 00:10-00:14]", sources)

        self.assertIn("hook eval returned chunk sources starting at or after 5 seconds", failures)

    def test_hook_eval_rejects_wrong_retrieval_policy(self) -> None:
        case = ASSIGNMENT_EVALS[2]
        sources = [
            {
                "type": "chunk",
                "video_id": "A",
                "start_time": 0.0,
                "source_tag": "[Video A, chunk 0, 00:00-00:04]",
            },
            {
                "type": "chunk",
                "video_id": "B",
                "start_time": 0.0,
                "source_tag": "[Video B, chunk 0, 00:00-00:04]",
            },
        ]

        failures = validate_eval_case(
            case,
            "A hook [Video A, chunk 0, 00:00-00:04]. B hook [Video B, chunk 0, 00:00-00:04].",
            sources,
            events=[{"event": "done", "data": {"ok": True}}],
            route="HOOK_COMPARISON",
            retrieval_policy="comparison_retrieval",
            enforce_route=True,
        )

        self.assertIn("expected retrieval policy hook_retrieval but got comparison_retrieval", failures)

    def test_hook_eval_requires_answer_to_cite_hook_chunks_only(self) -> None:
        case = ASSIGNMENT_EVALS[2]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {
                "type": "chunk",
                "video_id": "A",
                "start_time": 0.0,
                "source_tag": "[Video A, chunk 0, 00:00-00:04]",
            },
            {
                "type": "chunk",
                "video_id": "B",
                "start_time": 0.0,
                "source_tag": "[Video B, chunk 0, 00:00-00:04]",
            },
        ]

        failures = validate_eval_case(
            case,
            "Video A has the sharper opening [Video A metadata].",
            sources,
            events=[{"event": "done", "data": {"ok": True}}],
            route="HOOK_COMPARISON",
            retrieval_policy=HOOK_RETRIEVAL,
            enforce_route=True,
        )

        self.assertIn("hook answer cited metadata instead of hook chunks only", failures)
        self.assertIn("answer did not cite a returned Video A transcript chunk", failures)
        self.assertIn("answer did not cite a returned Video B transcript chunk", failures)

    def test_mixed_eval_requires_chunks_from_both_videos(self) -> None:
        case = ASSIGNMENT_EVALS[4]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
            {
                "type": "chunk",
                "video_id": "A",
                "start_time": 0.0,
                "source_tag": "[Video A, chunk 0, 00:00-00:04]",
            },
        ]

        failures = validate_eval_case(case, "Improve B using [Video A, chunk 0, 00:00-00:04]", sources)

        self.assertIn("missing transcript chunk source for Video B", failures)

    def test_improvement_eval_requires_answer_chunk_citations_from_both_videos(self) -> None:
        case = ASSIGNMENT_EVALS[4]
        sources = [
            {"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"},
            {"type": "metadata", "video_id": "B", "source_tag": "[Video B metadata]"},
            {
                "type": "chunk",
                "video_id": "A",
                "start_time": 0.0,
                "source_tag": "[Video A, chunk 0, 00:00-00:04]",
            },
            {
                "type": "chunk",
                "video_id": "B",
                "start_time": 0.0,
                "source_tag": "[Video B, chunk 0, 00:00-00:04]",
            },
        ]

        failures = validate_eval_case(
            case,
            "Improve B by copying A's opening clarity [Video A, chunk 0, 00:00-00:04].",
            sources,
            events=[{"event": "done", "data": {"ok": True}}],
            route="IMPROVEMENT_SUGGESTION",
            retrieval_policy=METADATA_AUGMENTED_RETRIEVAL,
            enforce_route=True,
        )

        self.assertIn("answer did not cite a returned Video B transcript chunk", failures)


if __name__ == "__main__":
    unittest.main()
