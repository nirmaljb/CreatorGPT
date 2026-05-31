import asyncio
import unittest
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

from backend.app.ingest.extractors import YouTubeExtractor
from backend.app.ingest.youtube_transcript import fetch_youtube_transcript


@dataclass
class TranscriptSegment:
    text: str
    start: float
    duration: float


class ProgressRecorder:
    async def set_video(self, video_id: str, current_step: str, local_percent: int) -> None:
        return None


class YouTubeLongCaptionsTests(unittest.TestCase):
    def test_fetch_youtube_transcript_is_unlimited_by_default(self) -> None:
        transcript = [
            TranscriptSegment("before cap", 590.0, 8.0),
            TranscriptSegment("after cap", 610.0, 6.0),
        ]
        with patch("backend.app.ingest.youtube_transcript._api.fetch", return_value=transcript):
            words = fetch_youtube_transcript("https://youtu.be/example123", "session-1", "A")

        self.assertIsNotNone(words)
        assert words is not None
        self.assertTrue(any(word["start"] >= 610.0 for word in words))

    def test_fetch_youtube_transcript_can_still_be_capped_explicitly(self) -> None:
        transcript = [
            TranscriptSegment("before cap", 590.0, 20.0),
            TranscriptSegment("after cap", 610.0, 6.0),
        ]
        with patch("backend.app.ingest.youtube_transcript._api.fetch", return_value=transcript):
            words = fetch_youtube_transcript("https://youtu.be/example123", "session-1", "A", max_seconds=600.0)

        self.assertIsNotNone(words)
        assert words is not None
        self.assertTrue(words)
        self.assertLessEqual(max(word["end"] for word in words), 600.0)
        self.assertFalse(any(word["start"] >= 610.0 for word in words))

    def test_long_youtube_with_captions_does_not_use_whisper_path(self) -> None:
        video = {"video_id": "A", "platform": "youtube", "url": "https://youtu.be/example123"}
        metadata = {"session_id": "session-1", "duration_seconds": 1200.0}
        caption_words = [{"text": "caption", "start": 700.0, "end": 701.0}]

        with (
            patch("backend.app.ingest.extractors.fetch_youtube_transcript", return_value=caption_words),
            patch.object(YouTubeExtractor, "groq_whisper_transcript", new_callable=AsyncMock) as whisper,
        ):
            result = asyncio.run(YouTubeExtractor().extract_transcript(video, metadata, ProgressRecorder()))

        self.assertEqual(result.source, "captions")
        self.assertEqual(result.words, caption_words)
        whisper.assert_not_called()


if __name__ == "__main__":
    unittest.main()
