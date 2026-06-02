import pytest
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.core.config import Settings


def test_startup_continues_when_qdrant_validation_fails_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_init_db() -> None:
        calls.append("postgres")

    def fake_ensure_collection() -> None:
        calls.append("qdrant")
        raise RuntimeError("qdrant dns failed")

    monkeypatch.setattr(main.database, "init_db", fake_init_db)
    monkeypatch.setattr(main, "ensure_collection", fake_ensure_collection)
    monkeypatch.setattr(main.settings, "require_qdrant_on_startup", False)

    main.startup()

    assert calls == ["postgres", "qdrant"]


def test_startup_can_fail_fast_when_qdrant_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_ensure_collection() -> None:
        raise RuntimeError("qdrant dns failed")

    monkeypatch.setattr(main.database, "init_db", lambda: None)
    monkeypatch.setattr(main, "ensure_collection", fake_ensure_collection)
    monkeypatch.setattr(main.settings, "require_qdrant_on_startup", True)

    with pytest.raises(RuntimeError, match="Qdrant startup validation failed"):
        main.startup()


def test_cors_allows_configured_render_frontend_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main.settings,
        "cors_origins",
        "http://localhost:3000,https://creator-rag-frontend.onrender.com/",
    )

    app = main.FastAPI()
    app.add_middleware(
        main.CORSMiddleware,
        allow_origins=main.settings.cors_origin_list,
        allow_origin_regex=main.settings.cors_origin_regex or None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/probe")
    def probe() -> dict:
        return {"ok": True}

    response = TestClient(app).options(
        "/probe",
        headers={
            "Origin": "https://creator-rag-frontend.onrender.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://creator-rag-frontend.onrender.com"


def test_cors_origin_regex_is_configurable() -> None:
    settings = Settings(CORS_ORIGIN_REGEX=r"https://.*\.onrender\.com")

    assert settings.cors_origin_regex == r"https://.*\.onrender\.com"
