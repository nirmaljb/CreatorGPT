import asyncio
import logging
import time
from pathlib import Path

from yt_dlp.utils import DownloadError

from backend.app.core.app_errors import (
    AppError,
    PipelineAppException,
    classify_ingest_error,
    classify_session_ingest_error,
    session_error_from_video_error,
)
from backend.app.core.config import get_settings
from backend.app.ingest.cache import (
    extraction_cache_key,
    failed_video_metadata,
    metadata_for_cache,
    metadata_from_cache,
)
from backend.app.ingest.chunker import chunk_transcript
from backend.app.ingest.extractors import TranscriptResult, get_platform_extractor
from backend.app.store.postgres import (
    create_session_usage_ledger,
    get_extraction_cache,
    record_video_usage,
    update_session_progress,
    update_session_status,
    update_video_ingest_status,
    upsert_extraction_cache,
    upsert_video_metadata,
)
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


def _cache_has_transcript(cache_entry: dict | None) -> bool:
    return cache_entry is not None and cache_entry.get("transcript_words") is not None


async def load_or_extract_metadata(
    session_id: str,
    video: dict,
) -> tuple[dict, dict | None]:
    settings = get_settings()
    video_id = video["video_id"]
    url = video["url"]
    platform = video["platform"]
    cache_key = extraction_cache_key(platform, url)
    extractor = get_platform_extractor(platform)

    cache_entry: dict | None = None
    if settings.force_refresh:
        logger.info(
            "FORCE_REFRESH enabled; bypassing extraction cache for Video %s session_id=%s platform=%s url=%s",
            video_id,
            session_id,
            platform,
            url,
        )
    else:
        cache_entry = await asyncio.to_thread(get_extraction_cache, cache_key)
        if cache_entry and cache_entry.get("normalized_metadata"):
            transcript_cached = _cache_has_transcript(cache_entry)
            logger.info(
                "Extraction cache hit for metadata Video %s session_id=%s "
                "platform=%s transcript_cached=%s cache_key=%s",
                video_id,
                session_id,
                platform,
                transcript_cached,
                cache_key,
            )
            metadata = metadata_from_cache(
                cache_entry["normalized_metadata"],
                session_id=session_id,
                video_id=video_id,
                url=url,
                cache_key=cache_key,
                raw_metadata=cache_entry.get("raw_metadata"),
                transcript_source=cache_entry.get("transcript_source") or "unavailable",
                transcript_cached=transcript_cached,
            )
            return metadata, cache_entry

        logger.info(
            "Extraction cache miss for metadata Video %s session_id=%s platform=%s cache_key=%s",
            video_id,
            session_id,
            platform,
            cache_key,
        )

    metadata = await asyncio.to_thread(extractor.extract_metadata, url, session_id, video_id)
    metadata["cache_key"] = cache_key
    await asyncio.to_thread(
        upsert_extraction_cache,
        cache_key,
        platform,
        url,
        metadata.get("raw_metadata"),
        metadata_for_cache(metadata),
        None,
        "unavailable",
    )
    logger.info(
        "Extraction cache stored metadata for Video %s session_id=%s platform=%s cache_key=%s",
        video_id,
        session_id,
        platform,
        cache_key,
    )
    return metadata, cache_entry


async def load_or_extract_transcript(
    video: dict,
    metadata: dict,
    cache_entry: dict | None,
    progress: SessionProgress,
) -> TranscriptResult:
    settings = get_settings()
    video_id = video["video_id"]
    platform = video["platform"]
    cache_key = metadata["cache_key"]

    if not settings.force_refresh and _cache_has_transcript(cache_entry):
        words = cache_entry.get("transcript_words") or []
        source = cache_entry.get("transcript_source") or "unavailable"
        await progress.set_video(video_id, f"Using cached transcript for Video {video_id}", 60)
        logger.info(
            "Extraction cache hit for transcript Video %s session_id=%s source=%s word_count=%s cache_key=%s",
            video_id,
            metadata["session_id"],
            source,
            len(words),
            cache_key,
        )
        return TranscriptResult(words=words, source=source)

    extractor = get_platform_extractor(platform)
    result = await extractor.extract_transcript(video, metadata, progress)
    await asyncio.to_thread(
        upsert_extraction_cache,
        cache_key,
        platform,
        video["url"],
        metadata.get("raw_metadata"),
        metadata_for_cache(metadata),
        result.words,
        result.source,
        None,
        True,
    )
    logger.info(
        "Extraction cache stored transcript for Video %s session_id=%s source=%s word_count=%s cache_key=%s",
        video_id,
        metadata["session_id"],
        result.source,
        len(result.words),
        cache_key,
    )
    return result


def _transcribed_seconds(result: TranscriptResult, metadata: dict, transcript_cached: bool) -> float:
    if transcript_cached or result.source != "whisper":
        return 0.0

    settings = get_settings()
    duration_seconds = float(metadata.get("duration_seconds") or 0.0)
    if duration_seconds > 0:
        return min(duration_seconds, float(settings.max_video_seconds))

    word_ends = [float(word.get("end") or 0.0) for word in result.words if isinstance(word, dict)]
    return max(word_ends, default=0.0)


async def process_video_transcript(
    video: dict,
    metadata: dict,
    cache_entry: dict | None,
    progress: SessionProgress,
) -> str | None:
    video_id = video["video_id"]
    video_started_at = time.monotonic()
    audio_path: str | None = None
    usage_recorded = False
    transcript_cached = False
    transcript_source = "unavailable"
    stage = "transcript"

    logger.info(
        "Transcript/vector pass for Video %s session_id=%s platform=%s url=%s",
        video_id,
        metadata["session_id"],
        metadata["platform"],
        video["url"],
    )

    try:
        await asyncio.to_thread(update_video_ingest_status, metadata["session_id"], video_id, "transcribing")
        result = await load_or_extract_transcript(video, metadata, cache_entry, progress)
        words = result.words
        transcript_source = result.source
        audio_path = result.audio_path
        metadata["transcript_source"] = transcript_source
        transcript_cached = not get_settings().force_refresh and _cache_has_transcript(cache_entry)
        await asyncio.to_thread(
            update_video_ingest_status,
            metadata["session_id"],
            video_id,
            "chunking",
            None,
            transcript_source,
            None,
            transcript_cached,
        )

        await progress.set_video(video_id, f"Chunking transcript for Video {video_id}", 70)
        chunks = chunk_transcript(words, metadata)
        max_chunks = get_settings().max_chunks_per_video
        original_chunk_count = len(chunks)
        if original_chunk_count > max_chunks:
            chunks = chunks[:max_chunks]
            logger.warning(
                "Applied chunk backpressure session_id=%s video_id=%s original_chunk_count=%s max_chunks_per_video=%s",
                metadata["session_id"],
                video_id,
                original_chunk_count,
                max_chunks,
            )
        logger.info(
            "Chunked transcript for Video %s session_id=%s transcript_source=%s word_count=%s chunk_count=%s",
            video_id,
            metadata["session_id"],
            transcript_source,
            len(words),
            len(chunks),
        )

        stage = "vector"
        await progress.set_video(video_id, f"Embedding chunks for Video {video_id}", 85)
        upserted = await asyncio.to_thread(upsert_chunks, chunks)
        await asyncio.to_thread(
            update_video_ingest_status,
            metadata["session_id"],
            video_id,
            "completed",
            None,
            transcript_source,
            upserted,
            transcript_cached,
        )
        await asyncio.to_thread(
            record_video_usage,
            metadata["session_id"],
            transcript_source,
            _transcribed_seconds(result, metadata, transcript_cached),
            upserted,
            upserted,
            int(transcript_cached),
            int(not transcript_cached),
            get_settings().embedding_model,
        )
        usage_recorded = True

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
    except Exception as exc:
        video_error = classify_ingest_error(exc, stage=stage, platform=metadata["platform"], video_id=video_id)
        logger.exception(
            "Transcript/vector pass failed for Video %s session_id=%s",
            video_id,
            metadata["session_id"],
        )
        await asyncio.to_thread(
            update_video_ingest_status,
            metadata["session_id"],
            video_id,
            "failed",
            str(exc),
            "unavailable",
            video_error=video_error,
        )
        if not usage_recorded:
            await asyncio.to_thread(
                record_video_usage,
                metadata["session_id"],
                transcript_source or "unavailable",
                0.0,
                0,
                0,
                int(transcript_cached),
                int(not transcript_cached),
                get_settings().embedding_model,
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
        raise PipelineAppException(video_error, exc) from exc


async def ingest_session_async(session_id: str, videos: list[dict]) -> None:
    audio_paths: list[str] = []
    started_at = time.monotonic()
    try:
        logger.info("Ingestion started session_id=%s video_count=%s", session_id, len(videos))
        await asyncio.to_thread(create_session_usage_ledger, session_id, len(videos))
        await asyncio.to_thread(
            update_session_status,
            session_id,
            "processing",
            None,
            "Starting ingestion",
            2,
        )

        metadata_by_video: dict[str, dict] = {}
        cache_by_video: dict[str, dict | None] = {}
        metadata_errors: list[AppError] = []
        for index, video in enumerate(videos):
            video_id = video["video_id"]
            url = video["url"]
            platform = video.get("platform")
            cache_key = extraction_cache_key(platform, url)
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
            try:
                metadata, cache_entry = await load_or_extract_metadata(session_id, video)
                await asyncio.to_thread(upsert_video_metadata, metadata)
                await asyncio.to_thread(
                    update_video_ingest_status,
                    session_id,
                    video_id,
                    "metadata_ready",
                    None,
                    metadata.get("transcript_source", "unavailable"),
                    0,
                    metadata.get("transcript_cached", False),
                )
                metadata_by_video[video_id] = metadata
                cache_by_video[video_id] = cache_entry
                logger.info(
                    "Stored metadata for Video %s session_id=%s metadata_cached=%s raw_metadata=%s",
                    video_id,
                    session_id,
                    metadata.get("metadata_cached", False),
                    bool(metadata.get("raw_metadata")),
                )
            except Exception as exc:
                video_error = classify_ingest_error(exc, stage="metadata", platform=platform, video_id=video_id)
                logger.exception("Metadata extraction failed for Video %s session_id=%s", video_id, session_id)
                await asyncio.to_thread(
                    upsert_video_metadata,
                    failed_video_metadata(
                        session_id=session_id,
                        video_id=video_id,
                        platform=platform,
                        url=url,
                        cache_key=cache_key,
                        error_message=str(exc),
                        video_error=video_error.to_dict(),
                    ),
                )
                await asyncio.to_thread(
                    record_video_usage,
                    session_id,
                    "unavailable",
                    0.0,
                    0,
                    0,
                    0,
                    1,
                    get_settings().embedding_model,
                )
                metadata_errors.append(video_error)

        if metadata_errors:
            session_error = session_error_from_video_error(metadata_errors[0])
            logger.error(
                "Metadata pass failed session_id=%s error_codes=%s",
                session_id,
                [error.code for error in metadata_errors],
            )
            await asyncio.to_thread(
                update_session_status,
                session_id,
                "failed",
                session_error.message,
                "Failed during metadata extraction",
                error=session_error,
            )
            return

        await asyncio.to_thread(update_session_progress, session_id, "Metadata ready for both videos", 25)
        logger.info("Metadata pass complete session_id=%s videos=%s", session_id, sorted(metadata_by_video))

        await asyncio.to_thread(get_embedder)
        progress = SessionProgress(session_id, [video["video_id"] for video in videos])
        results = await asyncio.gather(
            *[
                process_video_transcript(
                    video,
                    metadata_by_video[video["video_id"]],
                    cache_by_video.get(video["video_id"]),
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

        await asyncio.to_thread(update_session_status, session_id, "completed", None, "Completed", 100)
        logger.info("Ingestion completed session_id=%s elapsed=%.2fs", session_id, time.monotonic() - started_at)
    except DownloadError as exc:
        video_error = classify_ingest_error(exc, stage="download")
        session_error = session_error_from_video_error(video_error)
        logger.exception("Video download/extraction failed session_id=%s", session_id)
        await asyncio.to_thread(
            update_session_status,
            session_id,
            "failed",
            session_error.message,
            "Failed during video download or extraction",
            error=session_error,
        )
    except Exception as exc:
        session_error = classify_session_ingest_error(exc)
        logger.exception("Ingestion failed session_id=%s", session_id)
        await asyncio.to_thread(
            update_session_status,
            session_id,
            "failed",
            session_error.message,
            "Failed during ingestion",
            error=session_error,
        )
    finally:
        for audio_path in audio_paths:
            try:
                await asyncio.to_thread(Path(audio_path).unlink, missing_ok=True)
                logger.info("Deleted temporary audio path=%s session_id=%s", audio_path, session_id)
            except OSError:
                logger.exception("Failed to delete temporary audio path=%s session_id=%s", audio_path, session_id)
