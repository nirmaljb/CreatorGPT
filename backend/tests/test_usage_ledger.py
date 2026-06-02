import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.store import database
from backend.app.store.models import Base
from backend.app.store.postgres import (
    create_session,
    create_session_usage_ledger,
    get_session_usage_ledger,
    record_chat_usage,
    record_video_usage,
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


def test_usage_ledger_accumulates_ingest_and_chat_usage(sqlite_database) -> None:
    create_session("session-1")
    create_session_usage_ledger("session-1", video_count=2)

    record_video_usage(
        session_id="session-1",
        transcript_source="captions",
        transcribed_seconds=0.0,
        chunk_count=5,
        embedding_count=5,
        cache_hit=1,
        cache_miss=0,
        embedding_model="embed-test",
    )
    record_video_usage(
        session_id="session-1",
        transcript_source="whisper",
        transcribed_seconds=28.12,
        chunk_count=3,
        embedding_count=3,
        cache_hit=0,
        cache_miss=1,
        embedding_model="embed-test",
    )
    record_chat_usage("session-1", prompt_tokens=120, completion_tokens=35, llm_model="llama-test")

    ledger = get_session_usage_ledger("session-1")

    assert ledger is not None
    assert ledger["session_id"] == "session-1"
    assert ledger["video_count"] == 2
    assert ledger["transcript_source"] == "captions,whisper"
    assert ledger["transcribed_seconds"] == pytest.approx(28.12)
    assert ledger["chunk_count"] == 8
    assert ledger["embedding_count"] == 8
    assert ledger["chat_prompt_tokens"] == 120
    assert ledger["chat_completion_tokens"] == 35
    assert ledger["llm_model"] == "llama-test"
    assert ledger["embedding_model"] == "embed-test"
    assert ledger["cache_hit"] == 1
    assert ledger["cache_miss"] == 1
    assert ledger["created_at"] is not None


def test_usage_ledger_keeps_unavailable_when_transcript_fails(sqlite_database) -> None:
    create_session("session-2")
    create_session_usage_ledger("session-2", video_count=1)

    record_video_usage(
        session_id="session-2",
        transcript_source="unavailable",
        cache_miss=1,
    )

    ledger = get_session_usage_ledger("session-2")

    assert ledger is not None
    assert ledger["transcript_source"] == "unavailable"
    assert ledger["transcribed_seconds"] == 0
    assert ledger["chunk_count"] == 0
    assert ledger["embedding_count"] == 0
    assert ledger["cache_miss"] == 1
