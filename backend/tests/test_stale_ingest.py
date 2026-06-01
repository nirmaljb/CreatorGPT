from datetime import datetime, timedelta, timezone

from backend.app.store.postgres import is_stale_processing_session


def test_processing_session_is_stale_after_timeout() -> None:
    now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    updated_at = now - timedelta(seconds=901)

    assert is_stale_processing_session("processing", updated_at, 900, now)


def test_non_processing_session_is_not_stale() -> None:
    now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    updated_at = now - timedelta(hours=1)

    assert not is_stale_processing_session("completed", updated_at, 900, now)


def test_processing_session_before_timeout_is_not_stale() -> None:
    now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    updated_at = now - timedelta(seconds=120)

    assert not is_stale_processing_session("processing", updated_at, 900, now)
