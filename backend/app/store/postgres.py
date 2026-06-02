import logging
import threading
from datetime import datetime, timezone

from sqlalchemy import select

from backend.app.core.config import get_settings
from backend.app.store.database import db_session
from backend.app.store.models import (
    ChatMessageModel,
    ExtractionCacheModel,
    SessionModel,
    SessionUsageLedgerModel,
    VideoMetadataModel,
)

logger = logging.getLogger(__name__)
_usage_ledger_lock = threading.Lock()

TERMINAL_VIDEO_STATUSES = {"completed", "failed"}
STALE_INGEST_MESSAGE = (
    "Ingestion stalled because the background worker stopped before completion. Start a new ingest session."
)
TRANSCRIPT_SOURCE_ORDER = ("captions", "whisper", "unavailable")


def create_session(session_id: str) -> None:
    with db_session() as db:
        db.add(
            SessionModel(
                id=session_id,
                status="processing",
                current_step="Queued",
                progress_percent=0,
            )
        )


def create_session_usage_ledger(session_id: str, video_count: int) -> None:
    settings = get_settings()
    with _usage_ledger_lock, db_session() as db:
        row = db.get(SessionUsageLedgerModel, session_id)
        if row is None:
            db.add(
                SessionUsageLedgerModel(
                    session_id=session_id,
                    video_count=video_count,
                    llm_model=settings.groq_chat_model,
                    embedding_model=settings.embedding_model,
                )
            )
            logger.info(
                "Created usage ledger session_id=%s video_count=%s llm_model=%s embedding_model=%s",
                session_id,
                video_count,
                settings.groq_chat_model,
                settings.embedding_model,
            )
            return

        row.video_count = video_count
        row.llm_model = row.llm_model or settings.groq_chat_model
        row.embedding_model = row.embedding_model or settings.embedding_model


def update_session_status(
    session_id: str,
    status: str,
    error_message: str | None = None,
    current_step: str | None = None,
    progress_percent: int | None = None,
) -> None:
    with db_session() as db:
        row = db.get(SessionModel, session_id)
        if row is None:
            row = SessionModel(id=session_id, status=status)
            db.add(row)
        row.status = status
        row.error_message = error_message
        if current_step is not None:
            row.current_step = current_step
        if progress_percent is not None:
            row.progress_percent = max(0, min(100, progress_percent))


def update_session_progress(session_id: str, current_step: str, progress_percent: int) -> None:
    update_session_status(
        session_id=session_id,
        status="processing",
        current_step=current_step,
        progress_percent=progress_percent,
    )


def _aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _usage_row_is_empty(row: SessionUsageLedgerModel) -> bool:
    return (
        row.transcribed_seconds == 0
        and row.chunk_count == 0
        and row.embedding_count == 0
        and row.chat_prompt_tokens == 0
        and row.chat_completion_tokens == 0
        and row.cache_hit == 0
        and row.cache_miss == 0
    )


def _merge_transcript_source(existing: str | None, incoming: str | None, replace_placeholder: bool) -> str:
    incoming_source = (incoming or "unavailable").strip() or "unavailable"
    existing_sources = {
        source.strip()
        for source in (existing or "").split(",")
        if source.strip() and not (replace_placeholder and source.strip() == "unavailable")
    }
    existing_sources.add(incoming_source)
    ordered = [source for source in TRANSCRIPT_SOURCE_ORDER if source in existing_sources]
    ordered.extend(sorted(existing_sources.difference(TRANSCRIPT_SOURCE_ORDER)))
    return ",".join(ordered) if ordered else "unavailable"


def record_video_usage(
    session_id: str,
    transcript_source: str,
    transcribed_seconds: float = 0.0,
    chunk_count: int = 0,
    embedding_count: int = 0,
    cache_hit: int = 0,
    cache_miss: int = 0,
    embedding_model: str | None = None,
) -> None:
    settings = get_settings()
    with _usage_ledger_lock, db_session() as db:
        row = db.get(SessionUsageLedgerModel, session_id)
        if row is None:
            row = SessionUsageLedgerModel(
                session_id=session_id,
                video_count=0,
                llm_model=settings.groq_chat_model,
                embedding_model=embedding_model or settings.embedding_model,
            )
            db.add(row)

        row.transcript_source = _merge_transcript_source(
            row.transcript_source,
            transcript_source,
            replace_placeholder=_usage_row_is_empty(row),
        )
        row.transcribed_seconds += max(0.0, float(transcribed_seconds or 0.0))
        row.chunk_count += max(0, int(chunk_count or 0))
        row.embedding_count += max(0, int(embedding_count or 0))
        row.cache_hit += max(0, int(cache_hit or 0))
        row.cache_miss += max(0, int(cache_miss or 0))
        row.embedding_model = embedding_model or row.embedding_model or settings.embedding_model
        logger.info(
            "Recorded video usage session_id=%s transcript_source=%s transcribed_seconds=%.2f "
            "chunk_count=%s embedding_count=%s cache_hit=%s cache_miss=%s",
            session_id,
            transcript_source,
            transcribed_seconds,
            chunk_count,
            embedding_count,
            cache_hit,
            cache_miss,
        )


def record_chat_usage(
    session_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    llm_model: str | None = None,
) -> None:
    settings = get_settings()
    with _usage_ledger_lock, db_session() as db:
        row = db.get(SessionUsageLedgerModel, session_id)
        if row is None:
            row = SessionUsageLedgerModel(
                session_id=session_id,
                video_count=0,
                llm_model=llm_model or settings.groq_chat_model,
                embedding_model=settings.embedding_model,
            )
            db.add(row)

        row.chat_prompt_tokens += max(0, int(prompt_tokens or 0))
        row.chat_completion_tokens += max(0, int(completion_tokens or 0))
        row.llm_model = llm_model or row.llm_model or settings.groq_chat_model
        row.embedding_model = row.embedding_model or settings.embedding_model
        logger.info(
            "Recorded chat usage session_id=%s prompt_tokens=%s completion_tokens=%s llm_model=%s",
            session_id,
            prompt_tokens,
            completion_tokens,
            row.llm_model,
        )


def is_stale_processing_session(
    status: str,
    updated_at: datetime | None,
    stale_after_seconds: int,
    now: datetime | None = None,
) -> bool:
    if status != "processing" or updated_at is None or stale_after_seconds <= 0:
        return False
    current_time = _aware_datetime(now or datetime.now(timezone.utc))
    updated_time = _aware_datetime(updated_at)
    return (current_time - updated_time).total_seconds() >= stale_after_seconds


def fail_stale_processing_session(session_id: str, stale_after_seconds: int) -> bool:
    with db_session() as db:
        row = db.get(SessionModel, session_id)
        if row is None or not is_stale_processing_session(row.status, row.updated_at, stale_after_seconds):
            return False

        row.status = "failed"
        row.error_message = STALE_INGEST_MESSAGE
        row.current_step = "Failed: ingestion stalled"

        videos = db.scalars(select(VideoMetadataModel).where(VideoMetadataModel.session_id == session_id)).all()
        for video in videos:
            if video.ingest_status in TERMINAL_VIDEO_STATUSES:
                continue
            video.ingest_status = "failed"
            video.video_error_message = STALE_INGEST_MESSAGE
            if not video.transcript_source:
                video.transcript_source = "unavailable"

        logger.warning(
            "Marked stale ingest session failed session_id=%s stale_after_seconds=%s video_count=%s",
            session_id,
            stale_after_seconds,
            len(videos),
        )
        return True


def upsert_video_metadata(metadata: dict) -> None:
    with db_session() as db:
        stmt = select(VideoMetadataModel).where(
            VideoMetadataModel.session_id == metadata["session_id"],
            VideoMetadataModel.video_id == metadata["video_id"],
        )
        row = db.scalar(stmt)
        if row is None:
            row = VideoMetadataModel(**metadata)
            db.add(row)
            return

        for key, value in metadata.items():
            setattr(row, key, value)


def update_video_ingest_status(
    session_id: str,
    video_id: str,
    ingest_status: str,
    error_message: str | None = None,
    transcript_source: str | None = None,
    chunk_count: int | None = None,
    transcript_cached: bool | None = None,
) -> None:
    with db_session() as db:
        row = db.scalar(
            select(VideoMetadataModel).where(
                VideoMetadataModel.session_id == session_id,
                VideoMetadataModel.video_id == video_id,
            )
        )
        if row is None:
            return
        row.ingest_status = ingest_status
        row.video_error_message = error_message
        if transcript_source is not None:
            row.transcript_source = transcript_source
        if chunk_count is not None:
            row.chunk_count = chunk_count
        if transcript_cached is not None:
            row.transcript_cached = transcript_cached


def _raw_has_value(raw_metadata: dict | None, *keys: str) -> bool:
    if not raw_metadata:
        return False
    return any(raw_metadata.get(key) is not None for key in keys)


def _video_to_dict(row: VideoMetadataModel) -> dict:
    raw_metadata = row.raw_metadata if isinstance(row.raw_metadata, dict) else None
    views_available = _raw_has_value(raw_metadata, "view_count")
    followers_available = _raw_has_value(
        raw_metadata,
        "uploader_subscriber_count",
        "channel_follower_count",
        "follower_count",
    )
    return {
        "session_id": row.session_id,
        "video_id": row.video_id,
        "url": row.url,
        "platform": row.platform,
        "creator": row.creator,
        "creator_followers": row.creator_followers,
        "creator_followers_available": followers_available,
        "views": row.views,
        "views_available": views_available,
        "likes": row.likes,
        "likes_available": _raw_has_value(raw_metadata, "like_count"),
        "comments": row.comments,
        "comments_available": _raw_has_value(raw_metadata, "comment_count"),
        "hashtags": row.hashtags or [],
        "upload_date": row.upload_date,
        "duration_seconds": row.duration_seconds,
        "engagement_rate": row.engagement_rate,
        "engagement_rate_available": views_available and row.views > 0,
        "ingest_status": row.ingest_status,
        "video_error_message": row.video_error_message,
        "transcript_source": row.transcript_source,
        "chunk_count": row.chunk_count,
        "metadata_cached": row.metadata_cached,
        "transcript_cached": row.transcript_cached,
        "has_raw_metadata": bool(row.raw_metadata),
    }


def _usage_ledger_to_dict(row: SessionUsageLedgerModel) -> dict:
    return {
        "session_id": row.session_id,
        "video_count": row.video_count,
        "transcribed_seconds": row.transcribed_seconds,
        "transcript_source": row.transcript_source,
        "chunk_count": row.chunk_count,
        "embedding_count": row.embedding_count,
        "chat_prompt_tokens": row.chat_prompt_tokens,
        "chat_completion_tokens": row.chat_completion_tokens,
        "llm_model": row.llm_model,
        "embedding_model": row.embedding_model,
        "cache_hit": row.cache_hit,
        "cache_miss": row.cache_miss,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def get_session_usage_ledger(session_id: str) -> dict | None:
    with db_session() as db:
        row = db.get(SessionUsageLedgerModel, session_id)
        if row is None:
            return None
        return _usage_ledger_to_dict(row)


def get_video_metadata(session_id: str) -> list[dict]:
    with db_session() as db:
        rows = db.scalars(
            select(VideoMetadataModel)
            .where(VideoMetadataModel.session_id == session_id)
            .order_by(VideoMetadataModel.video_id)
        ).all()
        return [_video_to_dict(row) for row in rows]


def get_session(session_id: str) -> dict | None:
    with db_session() as db:
        row = db.get(SessionModel, session_id)
        if row is None:
            return None
        videos = db.scalars(
            select(VideoMetadataModel)
            .where(VideoMetadataModel.session_id == session_id)
            .order_by(VideoMetadataModel.video_id)
        ).all()
        return {
            "session_id": row.id,
            "status": row.status,
            "error_message": row.error_message,
            "current_step": row.current_step,
            "progress_percent": row.progress_percent,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "metadata": [_video_to_dict(video) for video in videos],
        }


def append_chat_message(
    session_id: str,
    role: str,
    content: str,
    sources: list[dict] | None = None,
) -> None:
    with db_session() as db:
        db.add(ChatMessageModel(session_id=session_id, role=role, content=content, sources=sources))


def _message_to_dict(row: ChatMessageModel) -> dict:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "role": row.role,
        "content": row.content,
        "sources": row.sources or [],
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def get_chat_messages(session_id: str, limit: int = 20) -> list[dict]:
    with db_session() as db:
        rows = db.scalars(
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.desc(), ChatMessageModel.id.desc())
            .limit(limit)
        ).all()
        return [_message_to_dict(row) for row in reversed(rows)]


def get_extraction_cache(cache_key: str) -> dict | None:
    with db_session() as db:
        row = db.get(ExtractionCacheModel, cache_key)
        if row is None:
            return None
        return {
            "cache_key": row.cache_key,
            "platform": row.platform,
            "url": row.url,
            "raw_metadata": row.raw_metadata,
            "normalized_metadata": row.normalized_metadata,
            "transcript_words": row.transcript_words,
            "transcript_source": row.transcript_source,
            "error_message": row.error_message,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }


def upsert_extraction_cache(
    cache_key: str,
    platform: str,
    url: str,
    raw_metadata: dict | None = None,
    normalized_metadata: dict | None = None,
    transcript_words: list[dict] | None = None,
    transcript_source: str = "unavailable",
    error_message: str | None = None,
    update_transcript: bool = False,
) -> None:
    with db_session() as db:
        row = db.get(ExtractionCacheModel, cache_key)
        if row is None:
            row = ExtractionCacheModel(
                cache_key=cache_key,
                platform=platform,
                url=url,
                raw_metadata=raw_metadata,
                normalized_metadata=normalized_metadata,
                transcript_words=transcript_words if update_transcript else None,
                transcript_source=transcript_source,
                error_message=error_message,
            )
            db.add(row)
            return

        row.platform = platform
        row.url = url
        row.error_message = error_message
        if raw_metadata is not None:
            row.raw_metadata = raw_metadata
        if normalized_metadata is not None:
            row.normalized_metadata = normalized_metadata
        if update_transcript:
            row.transcript_words = transcript_words
            row.transcript_source = transcript_source
