from fastapi.testclient import TestClient

from backend.app import main
from backend.app.core.backpressure import reset_backpressure_state
from backend.app.core.url_validation import is_valid_instagram_reel_url, is_valid_youtube_url, validate_ingest_videos


def _valid_payload() -> dict:
    return {
        "videos": [
            {"video_id": "A", "platform": "youtube", "url": "https://www.youtube.com/watch?v=abc123&si=share"},
            {"video_id": "B", "platform": "instagram", "url": "https://www.instagram.com/reel/def456/?igsh=test"},
        ]
    }


def test_youtube_validation_accepts_common_url_forms() -> None:
    assert is_valid_youtube_url(" https://www.youtube.com/watch?v=abc123&si=share ")
    assert is_valid_youtube_url("https://m.youtube.com/watch?v=abc123")
    assert is_valid_youtube_url("HTTPS://YOUTUBE.COM/shorts/abc123?feature=share")
    assert is_valid_youtube_url("https://youtu.be/abc123?t=12")


def test_instagram_validation_accepts_reels_only() -> None:
    assert is_valid_instagram_reel_url(" https://www.instagram.com/reel/abc123/?igsh=test ")
    assert is_valid_instagram_reel_url("HTTPS://INSTAGRAM.COM/reel/abc123")
    assert not is_valid_instagram_reel_url("https://www.instagram.com/p/abc123/")
    assert not is_valid_instagram_reel_url("https://www.instagram.com/stories/user/123/")


def test_validate_ingest_videos_trims_urls_and_preserves_query_strings() -> None:
    videos, error = validate_ingest_videos(_valid_payload()["videos"])

    assert error is None
    assert videos[0]["url"] == "https://www.youtube.com/watch?v=abc123&si=share"
    assert videos[1]["url"] == "https://www.instagram.com/reel/def456/?igsh=test"


def test_ingest_rejects_platform_url_mismatch_before_side_effects(monkeypatch) -> None:
    side_effects: list[str] = []

    def side_effect(name: str):
        def _inner(*args, **kwargs):
            side_effects.append(name)
            raise AssertionError(f"{name} should not run for invalid URL input")

        return _inner

    payload = _valid_payload()
    payload["videos"][0]["platform"] = "instagram"

    monkeypatch.setattr(main, "try_acquire_ingest_slot", side_effect("slot"))
    monkeypatch.setattr(main, "check_session_rate_limit", side_effect("rate"))
    monkeypatch.setattr(main, "create_session", side_effect("create"))

    response = TestClient(main.app).post("/ingest", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_PLATFORM_URL_MISMATCH"
    assert response.json()["error"]["video_id"] == "A"
    assert response.json()["error"]["field"] == "videos[0].url"
    assert side_effects == []


def test_ingest_rejects_non_reel_instagram_url() -> None:
    payload = _valid_payload()
    payload["videos"][1]["url"] = "https://www.instagram.com/p/not-a-reel/"

    response = TestClient(main.app).post("/ingest", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_INVALID_URL"
    assert "Instagram Reel" in response.json()["error"]["message"]


def test_ingest_allows_same_platform_comparisons(monkeypatch) -> None:
    reset_backpressure_state()
    created_sessions: list[str] = []
    background_calls: list[tuple[str, list[dict]]] = []

    def fake_create_session(session_id: str) -> None:
        created_sessions.append(session_id)

    async def fake_ingest_session(session_id: str, videos: list[dict]) -> None:
        background_calls.append((session_id, videos))

    payload = {
        "videos": [
            {"video_id": "A", "platform": "youtube", "url": "https://youtube.com/watch?v=abc123"},
            {"video_id": "B", "platform": "youtube", "url": "https://youtu.be/def456?t=9"},
        ]
    }

    monkeypatch.setattr(main.settings, "max_concurrent_ingestions", 10)
    monkeypatch.setattr(main.settings, "max_sessions_per_ip_per_hour", 10)
    monkeypatch.setattr(main, "create_session", fake_create_session)
    monkeypatch.setattr(main, "ingest_session", fake_ingest_session)

    try:
        response = TestClient(main.app).post("/ingest", json=payload)
    finally:
        reset_backpressure_state()

    assert response.status_code == 200
    assert created_sessions
    assert background_calls[0][1][1]["platform"] == "youtube"
