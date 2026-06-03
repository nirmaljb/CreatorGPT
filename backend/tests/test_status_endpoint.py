from fastapi.testclient import TestClient

from backend.app import main


def test_status_reloads_after_stale_processing_guard(monkeypatch) -> None:
    session_id = "session-stale"
    sessions = [
        {
            "session_id": session_id,
            "status": "processing",
            "error_message": None,
            "current_step": "Finished Video B",
            "progress_percent": 66,
            "metadata": [],
        },
        {
            "session_id": session_id,
            "status": "failed",
            "error_message": "Ingestion stalled",
            "current_step": "Failed: ingestion stalled",
            "progress_percent": 66,
            "metadata": [],
        },
    ]
    stale_calls: list[tuple[str, int]] = []

    def fake_get_session(requested_session_id: str) -> dict:
        assert requested_session_id == session_id
        return sessions.pop(0)

    def fake_fail_stale_processing_session(requested_session_id: str, stale_after_seconds: int) -> bool:
        stale_calls.append((requested_session_id, stale_after_seconds))
        return True

    monkeypatch.setattr(main, "get_session", fake_get_session)
    monkeypatch.setattr(main, "fail_stale_processing_session", fake_fail_stale_processing_session)
    monkeypatch.setattr(main.settings, "ingest_stale_seconds", 123)

    client = TestClient(main.app)
    response = client.get(f"/status/{session_id}")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["status"] == "failed"
    assert stale_calls == [(session_id, 123)]
