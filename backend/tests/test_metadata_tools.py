import unittest
from unittest.mock import patch

from backend.app.rag.metadata_tools import (
    get_creator_info,
    get_engagement_comparison,
    get_session_video_summary,
    get_video_metrics,
)

VIDEO_ROWS = [
    {
        "video_id": "A",
        "platform": "youtube",
        "creator": "Creator A",
        "creator_followers": 100,
        "views": 1000,
        "likes": 90,
        "comments": 10,
        "hashtags": ["#a"],
        "upload_date": "2026-01-01",
        "duration_seconds": 60.0,
        "engagement_rate": 10.0,
        "ingest_status": "completed",
        "transcript_source": "captions",
        "chunk_count": 5,
    },
    {
        "video_id": "B",
        "platform": "instagram",
        "creator": "Creator B",
        "creator_followers": 0,
        "views": 0,
        "likes": 20,
        "comments": 2,
        "hashtags": [],
        "upload_date": None,
        "duration_seconds": 30.0,
        "engagement_rate": 0.0,
        "ingest_status": "completed",
        "transcript_source": "whisper",
        "chunk_count": 3,
    },
]


class MetadataToolsTests(unittest.TestCase):
    def test_get_video_metrics_returns_cited_postgres_fields(self) -> None:
        with patch("backend.app.rag.metadata_tools.get_video_metadata", return_value=VIDEO_ROWS):
            result = get_video_metrics("session-1")

        self.assertEqual(result[0]["views"], 1000)
        self.assertEqual(result[0]["engagement_rate_percent"], 10.0)
        self.assertEqual(result[0]["source_tag"], "[Video A metadata]")

    def test_get_creator_info_marks_missing_followers_unavailable(self) -> None:
        with patch("backend.app.rag.metadata_tools.get_video_metadata", return_value=VIDEO_ROWS):
            result = get_creator_info("session-1", "B")

        self.assertEqual(result["creator"], "Creator B")
        self.assertEqual(result["creator_followers"], "unavailable")
        self.assertEqual(result["source_tag"], "[Video B metadata]")

    def test_get_engagement_comparison_uses_metadata_rows(self) -> None:
        with patch("backend.app.rag.metadata_tools.get_video_metadata", return_value=VIDEO_ROWS):
            result = get_engagement_comparison("session-1")

        self.assertEqual(result["highest_engagement_video_id"], "A")
        self.assertEqual(len(result["videos"]), 2)

    def test_get_session_video_summary_includes_ingest_context(self) -> None:
        with patch("backend.app.rag.metadata_tools.get_video_metadata", return_value=VIDEO_ROWS):
            result = get_session_video_summary("session-1")

        self.assertEqual(result[1]["transcript_source"], "whisper")
        self.assertEqual(result[1]["chunk_count"], 3)


if __name__ == "__main__":
    unittest.main()
