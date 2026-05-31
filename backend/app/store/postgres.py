from sqlalchemy import select

from backend.app.store.database import db_session
from backend.app.store.models import ChatMessageModel, ExtractionCacheModel, SessionModel, VideoMetadataModel


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


def _video_to_dict(row: VideoMetadataModel) -> dict:
    return {
        "session_id": row.session_id,
        "video_id": row.video_id,
        "url": row.url,
        "platform": row.platform,
        "creator": row.creator,
        "creator_followers": row.creator_followers,
        "views": row.views,
        "likes": row.likes,
        "comments": row.comments,
        "hashtags": row.hashtags or [],
        "upload_date": row.upload_date,
        "duration_seconds": row.duration_seconds,
        "engagement_rate": row.engagement_rate,
        "ingest_status": row.ingest_status,
        "video_error_message": row.video_error_message,
        "transcript_source": row.transcript_source,
        "chunk_count": row.chunk_count,
        "metadata_cached": row.metadata_cached,
        "transcript_cached": row.transcript_cached,
        "has_raw_metadata": bool(row.raw_metadata),
    }


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
        return {
            "session_id": row.id,
            "status": row.status,
            "error_message": row.error_message,
            "current_step": row.current_step,
            "progress_percent": row.progress_percent,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "metadata": get_video_metadata(session_id),
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
