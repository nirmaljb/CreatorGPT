from fastapi.testclient import TestClient

from backend.app import main
from backend.app.core.backpressure import release_ingest_slot, reset_backpressure_state, try_acquire_ingest_slot


def _ingest_payload() -> dict:
    return {
        "videos": [
            {"video_id": "A", "platform": "youtube", "url": "https://youtu.be/example123"},
            {"video_id": "B", "platform": "instagram", "url": "https://instagram.com/reel/example123/"},
        ]
    }


def test_config_exposes_runtime_backpressure_limits(monkeypatch) -> None:
    monkeypatch.setattr(main.settings, "max_video_seconds", 321)
    monkeypatch.setattr(main.settings, "max_concurrent_ingestions", 3)
    monkeypatch.setattr(main.settings, "max_chunks_per_video", 77)
    monkeypatch.setattr(main.settings, "max_chat_history_messages", 9)
    monkeypatch.setattr(main.settings, "max_retrieved_chunks", 5)
    monkeypatch.setattr(main.settings, "max_sessions_per_ip_per_hour", 11)

    response = TestClient(main.app).get("/config")

    assert response.status_code == 200
    assert response.json()["limits"] == {
        "max_video_seconds": 321,
        "max_concurrent_ingestions": 3,
        "max_chunks_per_video": 77,
        "max_chat_history_messages": 9,
        "max_retrieved_chunks": 5,
        "max_sessions_per_ip_per_hour": 11,
    }


def test_ingest_rejects_when_concurrent_limit_is_full(monkeypatch) -> None:
    reset_backpressure_state()
    monkeypatch.setattr(main.settings, "max_concurrent_ingestions", 1)
    assert try_acquire_ingest_slot(1)

    try:
        response = TestClient(main.app).post("/ingest", json=_ingest_payload())
    finally:
        release_ingest_slot()
        reset_backpressure_state()

    assert response.status_code == 429
    assert "Too many ingestions" in response.json()["detail"]
    assert response.json()["error"]["code"] == "INGEST_BUSY"
    assert response.json()["error"]["retryable"]


def test_ingest_rejects_sessions_over_ip_hourly_limit(monkeypatch) -> None:
    reset_backpressure_state()
    created_sessions: list[str] = []
    background_calls: list[tuple[str, list[dict]]] = []

    def fake_create_session(session_id: str) -> None:
        created_sessions.append(session_id)

    def fake_ingest_session(session_id: str, videos: list[dict]) -> None:
        background_calls.append((session_id, videos))

    monkeypatch.setattr(main.settings, "max_concurrent_ingestions", 10)
    monkeypatch.setattr(main.settings, "max_sessions_per_ip_per_hour", 1)
    monkeypatch.setattr(main, "create_session", fake_create_session)
    monkeypatch.setattr(main, "ingest_session", fake_ingest_session)

    try:
        client = TestClient(main.app)
        first = client.post("/ingest", json=_ingest_payload())
        second = client.post("/ingest", json=_ingest_payload())
    finally:
        reset_backpressure_state()

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["Retry-After"]
    assert "Session rate limit" in second.json()["detail"]
    assert second.json()["error"]["code"] == "INGEST_RATE_LIMITED"
    assert second.json()["error"]["retry_after_seconds"] == int(second.headers["Retry-After"])
    assert len(created_sessions) == 1
    assert len(background_calls) == 1
