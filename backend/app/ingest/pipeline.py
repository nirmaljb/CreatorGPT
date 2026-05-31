import asyncio
import logging
import time
from pathlib import Path

from yt_dlp.utils import DownloadError

from backend.app.ingest.chunker import chunk_transcript
from backend.app.ingest.downloader import download_audio
from backend.app.ingest.metadata import scrape_metadata
from backend.app.ingest.transcriber import transcribe
from backend.app.ingest.youtube_transcript import fetch_youtube_transcript
from backend.app.store.postgres import update_session_progress, update_session_status, upsert_video_metadata
from backend.app.store.vector import get_embedder, upsert_chunks

logger = logging.getLogger(__name__)


class SessionProgress:
    def __init__(self, session_id: str, video_ids: list[str]) -> None:
        self.session_id = session_id
        self.video_progress = {video_id: 0 for video_id in video_ids}
        self.lock = asyncio.Lock()

    async def set_overall(self, current_step: str, progress_percent: int) -> None:
        await asyncio.to_thread(
            update_session_progress,
            self.session_id,
            current_step,
            progress_percent,
        )

    async def set_video(self, video_id: str, current_step: str, local_percent: int) -> None:
        async with self.lock:
            self.video_progress[video_id] = max(self.video_progress.get(video_id, 0), local_percent)
            average_video_progress = sum(self.video_progress.values()) / max(len(self.video_progress), 1)
            aggregate = min(99, 25 + round(average_video_progress * 0.74))

        await self.set_overall(current_step, aggregate)


def ingest_session(session_id: str, videos: list[dict]) -> None:
    asyncio.run(ingest_session_async(session_id, videos))


async def get_transcript_words(
    video: dict,
    metadata: dict,
    progress: SessionProgress,
) -> tuple[list[dict], str, str | None]:
    video_id = video["video_id"]
    url = video["url"]
    platform = (metadata.get("platform") or video.get("platform") or "").lower()

    if platform == "youtube":
        await progress.set_video(video_id, f"Fetching YouTube captions for Video {video_id}", 8)
        caption_words = await asyncio.to_thread(fetch_youtube_transcript, url, metadata["session_id"], video_id)
        if caption_words:
            await progress.set_video(video_id, f"Using YouTube captions for Video {video_id}", 55)
            return caption_words, "youtube_captions", None

        logger.info(
            "Falling back to Whisper for Video %s session_id=%s after YouTube transcript miss",
            video_id,
            metadata["session_id"],
        )
        await progress.set_video(video_id, f"Captions unavailable; downloading audio for Video {video_id}", 12)
    else:
        await progress.set_video(video_id, f"Downloading audio for Video {video_id}", 12)

    audio_path = await asyncio.to_thread(
        download_audio,
        url,
        metadata["session_id"],
        video_id,
        metadata["duration_seconds"],
    )

    await progress.set_video(video_id, f"Transcribing Video {video_id} with Whisper", 45)
    words = await asyncio.to_thread(transcribe, audio_path)
    return words, "whisper", audio_path


async def process_video_transcript(
    video: dict,
    metadata: dict,
    progress: SessionProgress,
) -> str | None:
    video_id = video["video_id"]
    video_started_at = time.monotonic()
    audio_path: str | None = None

    logger.info(
        "Transcript/vector pass for Video %s session_id=%s platform=%s url=%s",
        video_id,
        metadata["session_id"],
        metadata["platform"],
        video["url"],
    )

    try:
        words, transcript_source, audio_path = await get_transcript_words(video, metadata, progress)
        metadata["transcript_source"] = transcript_source

        await progress.set_video(video_id, f"Chunking transcript for Video {video_id}", 70)
        chunks = chunk_transcript(words, metadata)
        logger.info(
            "Chunked transcript for Video %s session_id=%s transcript_source=%s word_count=%s chunk_count=%s",
            video_id,
            metadata["session_id"],
            transcript_source,
            len(words),
            len(chunks),
        )

        await progress.set_video(video_id, f"Embedding chunks for Video {video_id}", 85)
        upserted = await asyncio.to_thread(upsert_chunks, chunks)

        await progress.set_video(video_id, f"Finished Video {video_id}", 100)
        logger.info(
            "Finished Video %s session_id=%s transcript_source=%s upserted_chunks=%s elapsed=%.2fs",
            video_id,
            metadata["session_id"],
            transcript_source,
            upserted,
            time.monotonic() - video_started_at,
        )
        return audio_path
    except Exception:
        logger.exception(
            "Transcript/vector pass failed for Video %s session_id=%s",
            video_id,
            metadata["session_id"],
        )
        if audio_path:
            try:
                await asyncio.to_thread(Path(audio_path).unlink, missing_ok=True)
                logger.info("Deleted failed temporary audio path=%s session_id=%s", audio_path, metadata["session_id"])
            except OSError:
                logger.exception(
                    "Failed to delete failed temporary audio path=%s session_id=%s",
                    audio_path,
                    metadata["session_id"],
                )
        raise


async def ingest_session_async(session_id: str, videos: list[dict]) -> None:
    audio_paths: list[str] = []
    started_at = time.monotonic()
    try:
        logger.info("Ingestion started session_id=%s video_count=%s", session_id, len(videos))
        await asyncio.to_thread(
            update_session_status,
            session_id,
            "processing",
            None,
            "Starting ingestion",
            2,
        )

        metadata_by_video: dict[str, dict] = {}
        for index, video in enumerate(videos):
            video_id = video["video_id"]
            url = video["url"]
            platform = video.get("platform")
            await asyncio.to_thread(
                update_session_progress,
                session_id,
                f"Reading metadata for Video {video_id}",
                8 + (index * 8),
            )
            logger.info(
                "Metadata pass for Video %s session_id=%s requested_platform=%s url=%s",
                video_id,
                session_id,
                platform,
                url,
            )
            metadata = await asyncio.to_thread(
                scrape_metadata,
                url,
                session_id,
                video_id,
                platform,
            )
            await asyncio.to_thread(upsert_video_metadata, metadata)
            metadata_by_video[video_id] = metadata
            logger.info("Stored metadata for Video %s session_id=%s", video_id, session_id)

        await asyncio.to_thread(update_session_progress, session_id, "Metadata ready for both videos", 25)
        logger.info("Metadata pass complete session_id=%s videos=%s", session_id, sorted(metadata_by_video))

        await asyncio.to_thread(get_embedder)
        progress = SessionProgress(session_id, [video["video_id"] for video in videos])
        results = await asyncio.gather(
            *[
                process_video_transcript(
                    video,
                    metadata_by_video[video["video_id"]],
                    progress,
                )
                for video in videos
            ],
            return_exceptions=True,
        )
        first_error: BaseException | None = None
        for result in results:
            if isinstance(result, BaseException):
                first_error = first_error or result
                continue
            if result:
                audio_paths.append(result)
        if first_error:
            raise first_error

        await asyncio.to_thread(update_session_status, session_id, "ready", None, "Ready", 100)
        logger.info("Ingestion ready session_id=%s elapsed=%.2fs", session_id, time.monotonic() - started_at)
    except DownloadError as exc:
        logger.exception("Video download/extraction failed session_id=%s", session_id)
        await asyncio.to_thread(
            update_session_status,
            session_id,
            "failed",
            f"Video download/extraction failed: {exc}",
            "Failed during video download or extraction",
        )
    except Exception as exc:
        logger.exception("Ingestion failed session_id=%s", session_id)
        await asyncio.to_thread(
            update_session_status,
            session_id,
            "failed",
            f"Ingestion failed: {exc}",
            "Failed during ingestion",
        )
    finally:
        for audio_path in audio_paths:
            try:
                await asyncio.to_thread(Path(audio_path).unlink, missing_ok=True)
                logger.info("Deleted temporary audio path=%s session_id=%s", audio_path, session_id)
            except OSError:
                logger.exception("Failed to delete temporary audio path=%s session_id=%s", audio_path, session_id)
