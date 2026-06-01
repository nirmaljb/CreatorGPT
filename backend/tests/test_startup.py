import pytest

from backend.app import main


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
