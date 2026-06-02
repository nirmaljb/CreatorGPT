import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.rag.graph import (
    COMPARISON_RETRIEVAL,
    FOLLOW_UP,
    HOOK_COMPARISON,
    HOOK_RETRIEVAL,
    IMPROVEMENT_SUGGESTION,
    METADATA_AUGMENTED_RETRIEVAL,
    METADATA_ONLY,
    MIXED_COMPARISON,
    TRANSCRIPT_ONLY,
    VIDEO_B_RETRIEVAL,
    _detect_video_ids,
    classify_query,
    resolve_follow_up,
    resolve_follow_up_query,
    retrieve_chunks,
    run_metadata_tools,
)


class RagGraphRoutingTests(unittest.TestCase):
    def test_detects_video_references(self) -> None:
        self.assertEqual(_detect_video_ids("Compare Video A and Video B"), {"A", "B"})
        self.assertEqual(_detect_video_ids("Suggest improvements for B based on what worked in A."), {"A", "B"})
        self.assertEqual(_detect_video_ids("What happens in Video B?"), {"B"})
        self.assertEqual(_detect_video_ids("What did A say?"), {"A"})
        self.assertEqual(_detect_video_ids("Summarize the transcript"), set())

    def test_assignment_questions_route_to_explicit_paths(self) -> None:
        cases = {
            "What's the engagement rate of each?": METADATA_ONLY,
            "Who is the creator of Video B and what is their follower count?": METADATA_ONLY,
            "Compare the hooks in the first 5 seconds.": HOOK_COMPARISON,
            "Why did Video A get more engagement than Video B?": MIXED_COMPARISON,
            "Suggest improvements for B based on what worked in A.": IMPROVEMENT_SUGGESTION,
        }

        for question, expected_route in cases.items():
            with self.subTest(question=question):
                self.assertEqual(classify_query(question), expected_route)

    def test_extended_eval_questions_route_to_expected_paths(self) -> None:
        cases = {
            (
                "Build a compact stats scorecard for both videos: views, likes, comments, "
                "engagement rate, and follower count."
            ): METADATA_ONLY,
            "How many shares did Video A get?": METADATA_ONLY,
            "Which one feels more watchable, and why?": TRANSCRIPT_ONLY,
            "Give each video a punchy tagline based only on what is said.": TRANSCRIPT_ONLY,
            (
                "First compare the opening hooks, then recommend two changes for Video B using "
                "A's strongest moment and the performance data."
            ): IMPROVEMENT_SUGGESTION,
            "If I only have time to remake one of these, what should I change first?": IMPROVEMENT_SUGGESTION,
            "Video B clearly won on engagement, right?": METADATA_ONLY,
        }

        for question, expected_route in cases.items():
            with self.subTest(question=question):
                self.assertEqual(classify_query(question), expected_route)

    def test_transcript_question_routes_to_transcript_only(self) -> None:
        self.assertEqual(classify_query("What does Video B discuss?"), TRANSCRIPT_ONLY)
        self.assertEqual(classify_query("Compare the topics in Video A and Video B."), TRANSCRIPT_ONLY)

    def test_metadata_route_does_not_call_qdrant_retrieve(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "How many views did Video A have?",
                    "route": METADATA_ONLY,
                }
            )

        self.assertEqual(state["chunks"], [])
        mocked_retrieve.assert_not_called()

    def test_hook_comparison_uses_hook_filter_for_both_videos(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "Compare the hooks in the first 5 seconds.",
                    "route": HOOK_COMPARISON,
                }
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual([chunk["hook_only"] for chunk in state["chunks"]], [True, True])
        self.assertEqual([chunk["top_k"] for chunk in state["chunks"]], [4, 4])
        self.assertEqual(state["retrieval_policy"], HOOK_RETRIEVAL)
        self.assertEqual(mocked_retrieve.call_count, 2)

    def test_mixed_question_uses_vector_retrieval_for_both_videos(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "Why did Video A get more engagement than Video B?",
                    "route": MIXED_COMPARISON,
                }
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual([chunk["hook_only"] for chunk in state["chunks"]], [False, False])
        self.assertEqual([chunk["top_k"] for chunk in state["chunks"]], [4, 4])
        self.assertEqual(state["retrieval_policy"], METADATA_AUGMENTED_RETRIEVAL)
        self.assertEqual(mocked_retrieve.call_count, 2)

    def test_transcript_comparison_uses_balanced_video_retrieval(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "Compare the topics in Video A and Video B.",
                    "route": TRANSCRIPT_ONLY,
                }
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual([chunk["top_k"] for chunk in state["chunks"]], [4, 4])
        self.assertEqual(state["retrieval_policy"], COMPARISON_RETRIEVAL)
        self.assertEqual(mocked_retrieve.call_count, 2)

    def test_vague_two_video_transcript_question_uses_balanced_retrieval(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "Which one feels more watchable, and why?",
                    "route": TRANSCRIPT_ONLY,
                }
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual([chunk["top_k"] for chunk in state["chunks"]], [4, 4])
        self.assertEqual(state["retrieval_policy"], COMPARISON_RETRIEVAL)
        self.assertEqual(mocked_retrieve.call_count, 2)

    def test_transcript_single_video_stays_filtered_to_that_video(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "What does Video B discuss?",
                    "route": TRANSCRIPT_ONLY,
                }
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["B"])
        self.assertEqual([chunk["top_k"] for chunk in state["chunks"]], [6])
        self.assertEqual(state["retrieval_policy"], VIDEO_B_RETRIEVAL)
        mocked_retrieve.assert_called_once()

    def test_improvement_route_retrieves_strong_a_and_weak_b_evidence(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "Suggest improvements for B based on what worked in A.",
                    "route": IMPROVEMENT_SUGGESTION,
                }
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual([chunk["top_k"] for chunk in state["chunks"]], [4, 4])
        self.assertEqual(state["retrieval_policy"], METADATA_AUGMENTED_RETRIEVAL)
        self.assertIn("strong evidence", state["chunks"][0]["query"])
        self.assertIn("improvement opportunity", state["chunks"][1]["query"])

    def test_retrieval_respects_lower_max_retrieved_chunks(self) -> None:
        with (
            patch("backend.app.rag.graph.get_settings", return_value=SimpleNamespace(max_retrieved_chunks=2)),
            patch("backend.app.rag.graph.retrieve") as mocked_retrieve,
        ):
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "Why did Video A get more engagement than Video B?",
                    "route": MIXED_COMPARISON,
                }
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual([chunk["top_k"] for chunk in state["chunks"]], [1, 1])
        self.assertEqual(len(state["chunks"]), 2)

    def test_metadata_tool_selection_uses_postgres_tools(self) -> None:
        with (
            patch("backend.app.rag.graph.get_engagement_comparison", return_value={"videos": []}) as engagement,
            patch("backend.app.rag.graph.get_video_metrics", return_value=[]) as metrics,
        ):
            state = run_metadata_tools(
                {
                    "session_id": "session-1",
                    "query": "What's the engagement rate of each?",
                    "route": METADATA_ONLY,
                }
            )

        self.assertEqual([item["tool"] for item in state["metadata_tool_results"]], ["get_engagement_comparison"])
        engagement.assert_called_once_with("session-1")
        metrics.assert_not_called()

    def test_creator_tool_can_target_single_video(self) -> None:
        with patch("backend.app.rag.graph.get_creator_info", return_value={"video_id": "B"}) as creator:
            state = run_metadata_tools(
                {"session_id": "session-1", "query": "Who's the creator of Video B?", "route": METADATA_ONLY}
            )

        self.assertEqual(state["metadata_tool_results"][0]["tool"], "get_creator_info")
        creator.assert_called_once_with("session-1", "B")

    def test_improvement_route_always_includes_engagement_and_summary_tools(self) -> None:
        with (
            patch("backend.app.rag.graph.get_engagement_comparison", return_value={"videos": []}) as engagement,
            patch("backend.app.rag.graph.get_session_video_summary", return_value=[]) as summary,
        ):
            state = run_metadata_tools(
                {
                    "session_id": "session-1",
                    "query": "Suggest improvements for B based on what worked in A.",
                    "route": IMPROVEMENT_SUGGESTION,
                }
            )

        self.assertEqual(
            [item["tool"] for item in state["metadata_tool_results"]],
            ["get_engagement_comparison", "get_session_video_summary"],
        )
        engagement.assert_called_once_with("session-1")
        summary.assert_called_once_with("session-1")

    def test_follow_up_question_is_detected_and_resolved_to_previous_video(self) -> None:
        history = [{"role": "user", "content": "Who is the creator of Video B?"}]

        self.assertEqual(classify_query("What's their follower count?", history=history), FOLLOW_UP)
        self.assertEqual(
            resolve_follow_up_query("What's their follower count?", history),
            "What's their follower count for Video B?",
        )

    def test_what_about_follow_up_reuses_previous_question_topic(self) -> None:
        history = [{"role": "user", "content": "Who is the creator of Video A?"}]

        state = resolve_follow_up(
            {
                "session_id": "session-1",
                "query": "What about B?",
                "history": history,
                "route": FOLLOW_UP,
            }
        )

        self.assertEqual(state["resolved_query"], "Who is the creator of Video B?")
        self.assertEqual(state["route"], METADATA_ONLY)


if __name__ == "__main__":
    unittest.main()
