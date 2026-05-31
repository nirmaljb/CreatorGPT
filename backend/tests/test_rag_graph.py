import unittest
from unittest.mock import patch

from backend.app.rag.graph import _detect_video_ids, retrieve_chunks


class RagGraphRoutingTests(unittest.TestCase):
    def test_detects_both_videos_when_comparing(self) -> None:
        self.assertEqual(_detect_video_ids("Compare Video A and Video B"), {"A", "B"})
        self.assertEqual(_detect_video_ids("What happens in Video B?"), {"B"})
        self.assertEqual(_detect_video_ids("Summarize the transcript"), set())

    def test_compare_query_retrieves_chunks_for_both_videos(self) -> None:
        with patch("backend.app.rag.graph.retrieve") as mocked_retrieve:
            mocked_retrieve.side_effect = lambda **kwargs: [kwargs]

            state = retrieve_chunks({"session_id": "session-1", "query": "Compare Video A and Video B"})

        self.assertEqual([chunk["video_id"] for chunk in state["chunks"]], ["A", "B"])
        self.assertEqual(mocked_retrieve.call_count, 2)


if __name__ == "__main__":
    unittest.main()
