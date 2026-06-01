import unittest
from unittest.mock import patch

from backend.app.rag.graph import _detect_video_ids, classify_query, retrieve_chunks, run_metadata_tools


class RagGraphRoutingTests(unittest.TestCase):
    def test_detects_both_videos_when_comparing(self) -> None:
        self.assertEqual(_detect_video_ids("Compare Video A and Video B"), {"A", "B"})
        self.assertEqual(_detect_video_ids("Suggest improvements for B based on what worked in A."), {"A", "B"})
        self.assertEqual(_detect_video_ids("What happens in Video B?"), {"B"})
        self.assertEqual(_detect_video_ids("Summarize the transcript"), set())

    def test_compare_query_retrieves_chunks_for_both_videos(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]

            state = retrieve_chunks(
                {"session_id": "session-1", "query": "Compare Video A and Video B", "route": "mixed"}
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual(mocked_retrieve.call_count, 2)

    def test_numeric_metadata_queries_are_metadata_route(self) -> None:
        questions = [
            "What's the engagement rate of each?",
            "Who's the creator of Video B?",
            "What's their follower count?",
            "How many views did Video A have?",
        ]

        for question in questions:
            with self.subTest(question=question):
                self.assertEqual(classify_query(question), "metadata")

    def test_metadata_route_does_not_call_qdrant_retrieve(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "How many views did Video A have?",
                    "route": "metadata",
                }
            )

        self.assertEqual(state["chunks"], [])
        mocked_retrieve.assert_not_called()

    def test_mixed_question_uses_vector_retrieval(self) -> None:
        self.assertEqual(classify_query("Compare Video A and Video B using transcript evidence"), "mixed")
        self.assertEqual(classify_query("Suggest improvements for B based on what worked in A."), "mixed")

        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]
            state = retrieve_chunks(
                {
                    "session_id": "session-1",
                    "query": "Compare Video A and Video B using transcript evidence",
                    "route": "mixed",
                }
            )

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual(mocked_retrieve.call_count, 2)

    def test_metadata_tool_selection_uses_postgres_tools(self) -> None:
        with (
            patch("backend.app.rag.graph.get_engagement_comparison", return_value={"videos": []}) as engagement,
            patch("backend.app.rag.graph.get_video_metrics", return_value=[]) as metrics,
        ):
            state = run_metadata_tools({"session_id": "session-1", "query": "What's the engagement rate of each?"})

        self.assertEqual([item["tool"] for item in state["metadata_tool_results"]], ["get_engagement_comparison"])
        engagement.assert_called_once_with("session-1")
        metrics.assert_not_called()

    def test_creator_tool_can_target_single_video(self) -> None:
        with patch("backend.app.rag.graph.get_creator_info", return_value={"video_id": "B"}) as creator:
            state = run_metadata_tools({"session_id": "session-1", "query": "Who's the creator of Video B?"})

        self.assertEqual(state["metadata_tool_results"][0]["tool"], "get_creator_info")
        creator.assert_called_once_with("session-1", "B")


if __name__ == "__main__":
    unittest.main()
