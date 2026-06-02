from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.app_errors import AppError
from backend.app.store import database
from backend.app.store.database import db_session
from backend.app.store.models import Base, SessionModel
from backend.app.store.postgres import (
    create_session,
    fail_stale_processing_session,
    get_session,
    update_session_status,
    upsert_video_metadata,
)


@pytest.fixture()
def sqlite_database(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(database, "_engine", engine)
    monkeypatch.setattr(database, "_session_factory", session_factory)
    yield
    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "_session_factory", None)


def _video_metadata(video_error: dict | None = None) -> dict:
    return {
        "session_id": "session-1",
        "video_id": "A",
        "url": "https://youtu.be/example",
        "platform": "youtube",
        "creator": "unknown",
        "creator_followers": 0,
        "views": 0,
        "likes": 0,
        "comments": 0,
        "hashtags": [],
        "duration_seconds": 0.0,
        "engagement_rate": 0.0,
        "raw_metadata": None,
        "ingest_status": "failed",
        "video_error_message": "raw provider detail",
        "video_error": video_error,
    }


def test_status_serializes_persisted_structured_session_and_video_errors(sqlite_database) -> None:
    create_session("session-1")
    session_error = AppError(
        code="INGEST_FAILED",
        message="Friendly session message.",
        scope="session",
        retryable=True,
    )
    video_error = AppError(
        code="INGEST_TRANSCRIPT_FAILED",
        message="Friendly video message.",
        scope="video",
        retryable=True,
        video_id="A",
    )

    update_session_status(
        "session-1",
        "failed",
        "raw session detail",
        "Failed during ingestion",
        error=session_error,
    )
    upsert_video_metadata(_video_metadata(video_error.to_dict()))

    session = get_session("session-1")

    assert session is not None
    assert session["error_message"] == "raw session detail"
    assert session["error"]["code"] == "INGEST_FAILED"
    assert session["metadata"][0]["video_error_message"] == "raw provider detail"
    assert session["metadata"][0]["video_error"]["code"] == "INGEST_TRANSCRIPT_FAILED"


def test_stale_ingest_persists_structured_retryable_errors(sqlite_database) -> None:
    create_session("session-1")
    upsert_video_metadata({**_video_metadata(), "ingest_status": "transcribing", "video_error_message": None})
    with db_session() as db:
        row = db.get(SessionModel, "session-1")
        assert row is not None
        row.updated_at = datetime.now(timezone.utc) - timedelta(seconds=1000)

    assert fail_stale_processing_session("session-1", stale_after_seconds=900)
    session = get_session("session-1")

    assert session is not None
    assert session["status"] == "failed"
    assert session["error"]["code"] == "INGEST_STALLED"
    assert session["error"]["retryable"]
    assert session["metadata"][0]["video_error"]["code"] == "INGEST_STALLED"
