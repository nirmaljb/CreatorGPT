import logging
from datetime import timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from backend.app.auth.scopes import REQUIRED_GOOGLE_OAUTH_SCOPES, missing_required_scopes, normalize_scope_string
from backend.app.auth.security import (
    clear_auth_cookies,
    new_token,
    require_csrf,
    session_cookie_from_request,
    set_auth_cookies,
)
from backend.app.core.config import get_settings
from backend.app.providers.google_oauth import GoogleOAuthConfigurationError, GoogleOAuthError, GoogleOAuthProvider
from backend.app.store.auth import (
    CONNECTION_DISCONNECTED,
    CONNECTION_RECONNECT_REQUIRED,
    consume_oauth_state,
    create_oauth_state,
    create_server_session,
    get_session_context,
    revoke_server_session,
    upsert_google_oauth_token,
    upsert_user_from_google,
    utc_now,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_google_provider() -> GoogleOAuthProvider:
    return GoogleOAuthProvider(get_settings())


def _redirect_uri(request: Request) -> str:
    settings = get_settings()
    return settings.google_oauth_redirect_uri.strip() or str(request.url_for("google_oauth_callback"))


def _frontend_url(params: dict[str, str], path: str = "/") -> str:
    base_url = get_settings().frontend_app_url.rstrip("/") or "http://localhost:3000"
    normalized_path = path if path.startswith("/") else f"/{path}"
    route_path = "" if normalized_path == "/" else normalized_path
    return f"{base_url}{route_path}?{urlencode(params)}"


def _connection_payload(oauth_token: dict | None) -> dict:
    if oauth_token is None:
        return {
            "connection_status": CONNECTION_DISCONNECTED,
            "granted_scopes": [],
            "missing_scopes": list(REQUIRED_GOOGLE_OAUTH_SCOPES),
            "reconnect_needed": True,
            "last_verified_at": None,
        }
    return {
        "connection_status": oauth_token["connection_status"],
        "granted_scopes": oauth_token["granted_scopes"],
        "missing_scopes": oauth_token["missing_scopes"],
        "reconnect_needed": oauth_token["reconnect_required"],
        "last_verified_at": oauth_token["last_verified_at"],
    }


def _public_user_payload(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "email_verified": user["email_verified"],
        "name": user["name"],
        "avatar_url": user["avatar_url"],
    }


@router.get("/auth/google/start")
def google_oauth_start(request: Request) -> RedirectResponse:
    state = new_token(32)
    code_verifier = new_token(64)
    redirect_uri = _redirect_uri(request)
    expires_at = utc_now() + timedelta(seconds=get_settings().oauth_state_ttl_seconds)
    create_oauth_state(state, code_verifier, redirect_uri, expires_at)
    try:
        authorization_url = get_google_provider().authorization_url(state, redirect_uri, code_verifier)
    except GoogleOAuthConfigurationError as exc:
        logger.warning("Google OAuth start failed with provider error type=%s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        ) from exc
    return RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)


@router.get("/auth/google/callback", name="google_oauth_callback")
def google_oauth_callback(request: Request, code: str | None = None, state: str | None = None) -> RedirectResponse:
    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth callback is missing code or state")
    oauth_state = consume_oauth_state(state)
    if oauth_state is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state is invalid or expired")

    try:
        provider = get_google_provider()
        token_response = provider.exchange_code_for_tokens(
            code,
            oauth_state["redirect_uri"],
            oauth_state["code_verifier"],
        )
        identity = provider.validate_identity(token_response.id_token, token_response.access_token)
    except GoogleOAuthError as exc:
        logger.warning("Google OAuth callback failed with provider error type=%s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google OAuth callback could not be completed",
        ) from exc

    granted_scopes = normalize_scope_string(token_response.scope or request.query_params.get("scope"))
    if not granted_scopes:
        granted_scopes = normalize_scope_string(request.query_params.get("scope"))
    user = upsert_user_from_google(identity)
    oauth_token = upsert_google_oauth_token(
        user_id=user["id"],
        granted_scopes=granted_scopes,
        refresh_token=token_response.refresh_token,
    )

    session_token = new_token(32)
    csrf_token = new_token(32)
    create_server_session(
        user_id=user["id"],
        session_token=session_token,
        csrf_token=csrf_token,
        expires_at=utc_now() + timedelta(seconds=get_settings().auth_session_ttl_seconds),
    )

    connection_status = oauth_token["connection_status"]
    if oauth_token["reconnect_required"] and not missing_required_scopes(granted_scopes):
        connection_status = CONNECTION_RECONNECT_REQUIRED
    response = RedirectResponse(
        _frontend_url({"auth": "connected", "connection": connection_status}, path="/app"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    set_auth_cookies(response, session_token=session_token, csrf_token=csrf_token)
    return response


@router.get("/me")
def me(request: Request, response: Response) -> dict:
    response.headers["Cache-Control"] = "no-store"
    context = get_session_context(session_cookie_from_request(request))
    if context is None:
        return {
            "authenticated": False,
            "user": None,
            "youtube": _connection_payload(None),
            "csrf_token": None,
        }
    return {
        "authenticated": True,
        "user": _public_user_payload(context["user"]),
        "youtube": _connection_payload(context["oauth_token"]),
        "csrf_token": request.cookies.get(get_settings().auth_csrf_cookie_name),
    }


@router.post("/auth/logout")
def logout(request: Request, response: Response) -> dict:
    context = get_session_context(session_cookie_from_request(request))
    if context is None:
        clear_auth_cookies(response)
        return {"ok": True}
    require_csrf(request, context["session"]["csrf_token_hash"])
    revoke_server_session(session_cookie_from_request(request))
    clear_auth_cookies(response)
    return {"ok": True}
