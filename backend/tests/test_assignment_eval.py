import unittest

from backend.evals.assignment_eval import ASSIGNMENT_EVALS, parse_sse, validate_eval_case


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


if __name__ == "__main__":
    unittest.main()
