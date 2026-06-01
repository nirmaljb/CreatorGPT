import json

import pytest
from fastapi.testclient import TestClient

from backend.app import main


@pytest.mark.smoke
def test_mocked_ingest_status_chat_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    created_sessions: set[str] = set()
    background_calls: list[tuple[str, list[dict]]] = []

    def fake_create_session(session_id: str) -> None:
        created_sessions.add(session_id)

    async def fake_ingest_session(session_id: str, videos: list[dict]) -> None:
        background_calls.append((session_id, videos))

    def fake_get_session(session_id: str) -> dict:
        return {
            "session_id": session_id,
            "status": "completed",
            "error_message": None,
            "current_step": "Completed",
            "progress_percent": 100,
            "metadata": [
                {
                    "video_id": "A",
                    "platform": "youtube",
                    "creator": "Creator A",
                    "creator_followers": 1000,
                    "views": 10000,
                    "likes": 900,
                    "comments": 100,
                    "engagement_rate": 10.0,
                    "transcript_source": "captions",
                    "chunk_count": 2,
                },
                {
                    "video_id": "B",
                    "platform": "instagram",
                    "creator": "Creator B",
                    "creator_followers": 0,
                    "views": 5000,
                    "likes": 200,
                    "comments": 20,
                    "engagement_rate": 4.4,
                    "transcript_source": "whisper",
                    "chunk_count": 1,
                },
            ],
        }

    def fake_stream_rag_response(session_id: str, message: str):
        assert session_id
        assert message
        sources = [{"type": "metadata", "video_id": "A", "source_tag": "[Video A metadata]"}]
        yield f"event: sources\ndata: {json.dumps({'sources': sources})}\n\n"
        yield 'event: token\ndata: {"token": "Video A engagement is 10.0% [Video A metadata]."}\n\n'
        yield 'event: done\ndata: {"ok": true}\n\n'

    monkeypatch.setattr(main, "create_session", fake_create_session)
    monkeypatch.setattr(main, "ingest_session", fake_ingest_session)
    monkeypatch.setattr(main, "get_session", fake_get_session)
    monkeypatch.setattr(main, "stream_rag_response", fake_stream_rag_response)

    client = TestClient(main.app)
    ingest_response = client.post(
        "/ingest",
        json={
            "videos": [
                {"video_id": "A", "platform": "youtube", "url": "https://youtu.be/example123"},
                {"video_id": "B", "platform": "instagram", "url": "https://instagram.com/reel/example123/"},
            ]
        },
    )
    assert ingest_response.status_code == 200
    session_id = ingest_response.json()["session_id"]
    assert session_id in created_sessions
    assert background_calls

    status_response = client.get(f"/status/{session_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    chat_response = client.post("/chat", json={"session_id": session_id, "message": "What is Video A engagement?"})
    assert chat_response.status_code == 200
    body = chat_response.text
    assert "event: sources" in body
    assert "event: token" in body
    assert "event: done" in body
    assert "[Video A metadata]" in body
