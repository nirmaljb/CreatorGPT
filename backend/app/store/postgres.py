from sqlalchemy import select

from backend.app.store.database import db_session
from backend.app.store.models import ChatMessageModel, SessionModel, VideoMetadataModel


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
