from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.store import database
from backend.app.store.models import Base
from backend.app.store.postgres import create_session, get_session, upsert_video_metadata


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


def test_get_session_loads_metadata_without_nested_metadata_helper(sqlite_database) -> None:
    create_session("session-1")
    upsert_video_metadata(
        {
            "session_id": "session-1",
            "video_id": "A",
            "url": "https://youtu.be/example",
            "platform": "youtube",
            "creator": "Creator A",
            "creator_followers": 100,
            "views": 1000,
            "likes": 100,
            "comments": 10,
            "hashtags": [],
            "duration_seconds": 60.0,
            "engagement_rate": 11.0,
            "raw_metadata": {"view_count": 1000, "like_count": 100, "comment_count": 10},
        }
    )

    with patch("backend.app.store.postgres.get_video_metadata", side_effect=AssertionError("nested call")):
        session = get_session("session-1")

    assert session is not None
    assert session["status"] == "processing"
    assert session["metadata"][0]["video_id"] == "A"
    assert session["metadata"][0]["views"] == 1000
