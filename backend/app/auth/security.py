import hashlib
import secrets

from fastapi import HTTPException, Request, Response, status

from backend.app.core.config import get_settings


def new_token(byte_count: int = 32) -> str:
    return secrets.token_urlsafe(byte_count)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    settings = get_settings()
    same_site = settings.auth_cookie_samesite.lower()
    if same_site not in {"lax", "strict", "none"}:
        same_site = "lax"
    response.set_cookie(
        settings.auth_session_cookie_name,
        session_token,
        max_age=settings.auth_session_ttl_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=same_site,
        path="/",
    )
    response.set_cookie(
        settings.auth_csrf_cookie_name,
        csrf_token,
        max_age=settings.auth_session_ttl_seconds,
        httponly=False,
        secure=settings.auth_cookie_secure,
        samesite=same_site,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.auth_session_cookie_name, path="/")
    response.delete_cookie(settings.auth_csrf_cookie_name, path="/")


def session_cookie_from_request(request: Request) -> str | None:
    return request.cookies.get(get_settings().auth_session_cookie_name)


def csrf_cookie_from_request(request: Request) -> str | None:
    return request.cookies.get(get_settings().auth_csrf_cookie_name)


def require_csrf(request: Request, expected_csrf_token: str | None) -> None:
    header_token = request.headers.get("x-csrf-token")
    cookie_token = csrf_cookie_from_request(request)
    if not header_token or not cookie_token or not expected_csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token is required")
    if not secrets.compare_digest(header_token, cookie_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token mismatch")
    if not secrets.compare_digest(hash_secret(header_token), expected_csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token mismatch")

