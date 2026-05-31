import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

from backend.app.ingest.downloader import download_audio
from backend.app.ingest.metadata import scrape_metadata
from backend.app.ingest.transcriber import transcribe
from backend.app.ingest.youtube_transcript import fetch_youtube_transcript

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    words: list[dict]
    source: str
    audio_path: str | None = None


class PlatformExtractor(Protocol):
    platform: str

    def extract_metadata(self, url: str, session_id: str, video_id: str) -> dict:
        raise NotImplementedError

    async def extract_transcript(self, video: dict, metadata: dict, progress: object) -> TranscriptResult:
        raise NotImplementedError


class YtDlpExtractor:
    platform = "unknown"

    def extract_metadata(self, url: str, session_id: str, video_id: str) -> dict:
        return scrape_metadata(url, session_id, video_id, self.platform)

    async def whisper_transcript(self, video: dict, metadata: dict, progress: object) -> TranscriptResult:
        video_id = video["video_id"]
        await progress.set_video(video_id, f"Downloading audio for Video {video_id}", 12)
        audio_path = await asyncio.to_thread(
            download_audio,
            video["url"],
            metadata["session_id"],
            video_id,
            metadata["duration_seconds"],
        )

        await progress.set_video(video_id, f"Transcribing Video {video_id} with Whisper", 45)
        words = await asyncio.to_thread(transcribe, audio_path)
        source = "whisper" if words else "unavailable"
        return TranscriptResult(words=words, source=source, audio_path=audio_path)


class YouTubeExtractor(YtDlpExtractor):
    platform = "youtube"

    async def extract_transcript(self, video: dict, metadata: dict, progress: object) -> TranscriptResult:
        video_id = video["video_id"]
        await progress.set_video(video_id, f"Fetching captions for Video {video_id}", 8)
        caption_words = await asyncio.to_thread(
            fetch_youtube_transcript,
            video["url"],
            metadata["session_id"],
            video_id,
        )
        if caption_words:
            await progress.set_video(video_id, f"Using captions for Video {video_id}", 55)
            return TranscriptResult(words=caption_words, source="captions")

        logger.info(
            "Caption transcript unavailable for Video %s session_id=%s; using Whisper path",
            video_id,
            metadata["session_id"],
        )
        return await self.whisper_transcript(video, metadata, progress)


class InstagramExtractor(YtDlpExtractor):
    platform = "instagram"

    async def extract_transcript(self, video: dict, metadata: dict, progress: object) -> TranscriptResult:
        return await self.whisper_transcript(video, metadata, progress)


def get_platform_extractor(platform: str) -> PlatformExtractor:
    normalized = platform.lower().strip()
    if normalized == "youtube":
        return YouTubeExtractor()
    if normalized == "instagram":
        return InstagramExtractor()
    raise ValueError(f"Unsupported platform: {platform}")
