from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app import main
from backend.app.auth import crypto as crypto_module
from backend.app.auth import routes
from backend.app.auth import security as security_module
from backend.app.auth.scopes import REQUIRED_GOOGLE_OAUTH_SCOPES
from backend.app.core.config import Settings
from backend.app.providers.google_oauth import GoogleIdentity, GoogleOAuthError, GoogleOAuthTokenResponse
from backend.app.store import database
from backend.app.store.auth import create_oauth_state, utc_now
from backend.app.store.database import db_session
from backend.app.store.models import Base, OAuthTokenModel, ServerSessionModel, UserModel


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


@pytest.fixture()
def auth_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    settings = Settings(
        GOOGLE_OAUTH_CLIENT_ID="client-id.apps.googleusercontent.com",
        GOOGLE_OAUTH_CLIENT_SECRET="client-secret",
        GOOGLE_OAUTH_REDIRECT_URI="http://testserver/auth/google/callback",
        FRONTEND_APP_URL="http://localhost:3000",
        TOKEN_ENCRYPTION_KEY="test-encryption-key",
        CORS_ORIGINS="http://localhost:3000",
    )
    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    monkeypatch.setattr(security_module, "get_settings", lambda: settings)
    monkeypatch.setattr(crypto_module, "get_settings", lambda: settings)
    return settings


class FakeGoogleProvider:
    def __init__(self, scope: str | None = None, refresh_token: str | None = "refresh-token-secret") -> None:
        self.scope = scope or " ".join(REQUIRED_GOOGLE_OAUTH_SCOPES)
        self.refresh_token = refresh_token
        self.exchange_calls: list[tuple[str, str, str]] = []

    def authorization_url(self, state: str, redirect_uri: str, code_verifier: str) -> str:
        return (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id=client-id.apps.googleusercontent.com&redirect_uri={redirect_uri}"
            f"&response_type=code&scope={'+'.join(REQUIRED_GOOGLE_OAUTH_SCOPES)}"
            f"&state={state}&access_type=offline&prompt=consent&code_challenge={code_verifier}"
            "&code_challenge_method=S256"
        )

    def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> GoogleOAuthTokenResponse:
        self.exchange_calls.append((code, redirect_uri, code_verifier))
        return GoogleOAuthTokenResponse(
            access_token="access-token-secret",
            refresh_token=self.refresh_token,
            id_token="id-token-secret",
            scope=self.scope,
            expires_in=3600,
        )

    def validate_identity(self, id_token: str, access_token: str) -> GoogleIdentity:
        assert id_token == "id-token-secret"
        assert access_token == "access-token-secret"
        return GoogleIdentity(
            subject="google-sub-123",
            email="creator@example.com",
            email_verified=True,
            name="Creator Example",
            avatar_url="https://example.test/avatar.png",
        )


def _state_from_redirect(response) -> str:
    location = response.headers["location"]
    query = parse_qs(urlparse(location).query)
    return query["state"][0]


def test_oauth_start_requests_only_required_read_only_scopes(
    sqlite_database,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeGoogleProvider()
    monkeypatch.setattr(routes, "get_google_provider", lambda: provider)

    response = TestClient(main.app).get("/auth/google/start", follow_redirects=False)

    assert response.status_code == 302
    query = parse_qs(urlparse(response.headers["location"]).query)
    requested_scopes = set(query["scope"][0].split())
    assert requested_scopes == set(REQUIRED_GOOGLE_OAUTH_SCOPES)
    assert "https://www.googleapis.com/auth/yt-analytics-monetary.readonly" not in requested_scopes
    assert "https://www.googleapis.com/auth/youtube.upload" not in requested_scopes
    assert "https://www.googleapis.com/auth/youtube.force-ssl" not in requested_scopes


def test_oauth_callback_rejects_invalid_state_before_provider_call(
    sqlite_database,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ProviderShouldNotRun(FakeGoogleProvider):
        def exchange_code_for_tokens(
            self,
            code: str,
            redirect_uri: str,
            code_verifier: str,
        ) -> GoogleOAuthTokenResponse:
            raise AssertionError("provider exchange should not run")

    monkeypatch.setattr(routes, "get_google_provider", lambda: ProviderShouldNotRun())

    response = TestClient(main.app).get("/auth/google/callback?code=code&state=wrong", follow_redirects=False)

    assert response.status_code == 400
    assert "state" in response.json()["detail"].lower()


def test_oauth_callback_creates_user_encrypted_token_and_server_session(
    sqlite_database,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeGoogleProvider()
    monkeypatch.setattr(routes, "get_google_provider", lambda: provider)
    client = TestClient(main.app)
    start_response = client.get("/auth/google/start", follow_redirects=False)
    state = _state_from_redirect(start_response)

    callback_response = client.get(f"/auth/google/callback?code=auth-code&state={state}", follow_redirects=False)

    assert callback_response.status_code == 303
    assert callback_response.headers["location"] == "http://localhost:3000?auth=connected&connection=connected"
    assert auth_settings.auth_session_cookie_name in callback_response.headers["set-cookie"]
    assert auth_settings.auth_csrf_cookie_name in callback_response.headers["set-cookie"]

    me_response = client.get("/me")
    assert me_response.status_code == 200
    assert me_response.headers["cache-control"] == "no-store"
    body = me_response.json()
    assert body["authenticated"] is True
    assert body["user"]["email"] == "creator@example.com"
    assert body["youtube"]["connection_status"] == "connected"
    assert body["youtube"]["missing_scopes"] == []
    assert "access-token-secret" not in me_response.text
    assert "refresh-token-secret" not in me_response.text
    assert "encrypted_refresh_token" not in body["youtube"]

    with db_session() as db:
        user = db.scalar(select(UserModel))
        token = db.scalar(select(OAuthTokenModel))
        session = db.scalar(select(ServerSessionModel))
        assert user is not None
        assert token is not None
        assert session is not None
        assert token.user_id == user.id
        assert token.granted_scopes == sorted(REQUIRED_GOOGLE_OAUTH_SCOPES)
        assert token.encrypted_refresh_token
        assert "refresh-token-secret" not in token.encrypted_refresh_token
        assert not hasattr(token, "access_token")
        assert session.session_token_hash
        assert session.csrf_token_hash


def test_oauth_callback_records_incomplete_connection_when_scopes_are_missing(
    sqlite_database,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    partial_scopes = "openid email profile https://www.googleapis.com/auth/youtube.readonly"
    provider = FakeGoogleProvider(scope=partial_scopes)
    monkeypatch.setattr(routes, "get_google_provider", lambda: provider)
    client = TestClient(main.app)
    state = _state_from_redirect(client.get("/auth/google/start", follow_redirects=False))

    response = client.get(f"/auth/google/callback?code=auth-code&state={state}", follow_redirects=False)

    assert response.status_code == 303
    body = client.get("/me").json()
    assert body["youtube"]["connection_status"] == "incomplete_scopes"
    assert body["youtube"]["reconnect_needed"] is True
    assert body["youtube"]["missing_scopes"] == ["https://www.googleapis.com/auth/yt-analytics.readonly"]


def test_oauth_callback_marks_reconnect_when_refresh_token_is_missing(
    sqlite_database,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeGoogleProvider(refresh_token=None)
    monkeypatch.setattr(routes, "get_google_provider", lambda: provider)
    client = TestClient(main.app)
    state = _state_from_redirect(client.get("/auth/google/start", follow_redirects=False))

    response = client.get(f"/auth/google/callback?code=auth-code&state={state}", follow_redirects=False)

    assert response.status_code == 303
    body = client.get("/me").json()
    assert body["youtube"]["connection_status"] == "reconnect_required"
    assert body["youtube"]["missing_scopes"] == []
    assert body["youtube"]["reconnect_needed"] is True


def test_authenticated_logout_requires_csrf(
    sqlite_database,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeGoogleProvider()
    monkeypatch.setattr(routes, "get_google_provider", lambda: provider)
    client = TestClient(main.app)
    state = _state_from_redirect(client.get("/auth/google/start", follow_redirects=False))
    client.get(f"/auth/google/callback?code=auth-code&state={state}", follow_redirects=False)

    missing_csrf = client.post("/auth/logout")
    assert missing_csrf.status_code == 403

    csrf_token = client.get("/me").json()["csrf_token"]
    logout = client.post("/auth/logout", headers={"x-csrf-token": csrf_token})
    assert logout.status_code == 200
    assert client.get("/me").json()["authenticated"] is False


def test_oauth_state_cannot_be_reused(
    sqlite_database,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingProvider(FakeGoogleProvider):
        def exchange_code_for_tokens(
            self,
            code: str,
            redirect_uri: str,
            code_verifier: str,
        ) -> GoogleOAuthTokenResponse:
            raise GoogleOAuthError("provider unavailable")

    monkeypatch.setattr(routes, "get_google_provider", lambda: FailingProvider())
    create_oauth_state(
        "state-once",
        "verifier",
        "http://testserver/auth/google/callback",
        utc_now() + timedelta(minutes=5),
    )
    client = TestClient(main.app)

    first = client.get("/auth/google/callback?code=code&state=state-once", follow_redirects=False)
    second = client.get("/auth/google/callback?code=code&state=state-once", follow_redirects=False)

    assert first.status_code == 502
    assert second.status_code == 400


def test_provider_errors_are_sanitized_in_callback_response(
    sqlite_database,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingProvider(FakeGoogleProvider):
        def exchange_code_for_tokens(
            self,
            code: str,
            redirect_uri: str,
            code_verifier: str,
        ) -> GoogleOAuthTokenResponse:
            raise GoogleOAuthError("raw refresh-token-secret provider payload")

    monkeypatch.setattr(routes, "get_google_provider", lambda: FailingProvider())
    client = TestClient(main.app)
    state = _state_from_redirect(client.get("/auth/google/start", follow_redirects=False))

    response = client.get(f"/auth/google/callback?code=auth-code&state={state}", follow_redirects=False)

    assert response.status_code == 502
    assert "refresh-token-secret" not in response.text
    assert response.json()["detail"] == "Google OAuth callback could not be completed"


def test_credentialed_cors_filters_wildcard_origins() -> None:
    settings = Settings(CORS_ORIGINS="*,https://app.example.com")

    assert "*" not in settings.cors_origin_list
    assert "https://app.example.com" in settings.cors_origin_list
