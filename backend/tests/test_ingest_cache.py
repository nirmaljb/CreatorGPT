import unittest

from backend.app.ingest.cache import extraction_cache_key, metadata_for_cache, metadata_from_cache


class IngestCacheTests(unittest.TestCase):
    def test_cache_key_includes_platform_url_and_duration_window(self) -> None:
        first = extraction_cache_key("youtube", "https://youtu.be/example", max_video_seconds=60)
        second = extraction_cache_key("instagram", "https://youtu.be/example", max_video_seconds=60)
        third = extraction_cache_key("youtube", "https://youtu.be/example", max_video_seconds=120)

        self.assertNotEqual(first, second)
        self.assertNotEqual(first, third)
        self.assertEqual(first, extraction_cache_key("youtube", "https://youtu.be/example", max_video_seconds=60))

    def test_cached_metadata_is_sessionized_without_cache_only_fields(self) -> None:
        original = {
            "session_id": "old",
            "video_id": "A",
            "url": "https://example.com/old",
            "platform": "youtube",
            "creator": "Creator",
            "views": 10,
            "raw_metadata": {"id": "raw"},
            "cache_key": "old-key",
            "metadata_cached": False,
        }

        cached = metadata_for_cache(original)
        self.assertNotIn("session_id", cached)
        self.assertNotIn("raw_metadata", cached)

        restored = metadata_from_cache(
            cached,
            session_id="new-session",
            video_id="B",
            url="https://example.com/new",
            cache_key="new-key",
            raw_metadata={"id": "raw"},
            transcript_source="captions",
            transcript_cached=True,
        )

        self.assertEqual(restored["session_id"], "new-session")
        self.assertEqual(restored["video_id"], "B")
        self.assertEqual(restored["url"], "https://example.com/new")
        self.assertEqual(restored["cache_key"], "new-key")
        self.assertTrue(restored["metadata_cached"])
        self.assertTrue(restored["transcript_cached"])
        self.assertEqual(restored["transcript_source"], "captions")


if __name__ == "__main__":
    unittest.main()
