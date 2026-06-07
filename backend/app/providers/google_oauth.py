import base64
import hashlib
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from backend.app.auth.scopes import REQUIRED_GOOGLE_OAUTH_SCOPES
from backend.app.core.config import Settings

GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_ENDPOINT = "https://oauth2.googleapis.com/tokeninfo"


class GoogleOAuthError(RuntimeError):
    pass


class GoogleOAuthConfigurationError(GoogleOAuthError):
    pass


@dataclass(frozen=True)
class GoogleOAuthTokenResponse:
    access_token: str
    refresh_token: str | None
    id_token: str
    scope: str
    expires_in: int | None = None


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str | None
    email_verified: bool
    name: str | None
    avatar_url: str | None


def code_challenge_for_verifier(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


class GoogleOAuthProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def authorization_url(self, state: str, redirect_uri: str, code_verifier: str) -> str:
        if not self._settings.google_oauth_client_id:
            raise GoogleOAuthConfigurationError("Google OAuth client ID is not configured")
        params = {
            "client_id": self._settings.google_oauth_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(REQUIRED_GOOGLE_OAUTH_SCOPES),
            "state": state,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "code_challenge": code_challenge_for_verifier(code_verifier),
            "code_challenge_method": "S256",
        }
        return f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

    def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> GoogleOAuthTokenResponse:
        if not self._settings.google_oauth_client_id or not self._settings.google_oauth_client_secret:
            raise GoogleOAuthConfigurationError("Google OAuth client credentials are not configured")
        payload = {
            "code": code,
            "client_id": self._settings.google_oauth_client_id,
            "client_secret": self._settings.google_oauth_client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }
        try:
            response = httpx.post(GOOGLE_TOKEN_ENDPOINT, data=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise GoogleOAuthError("Google OAuth token exchange failed") from exc

        access_token = data.get("access_token")
        id_token = data.get("id_token")
        if not access_token or not id_token:
            raise GoogleOAuthError("Google OAuth token response was incomplete")
        return GoogleOAuthTokenResponse(
            access_token=access_token,
            refresh_token=data.get("refresh_token"),
            id_token=id_token,
            scope=data.get("scope") or "",
            expires_in=data.get("expires_in"),
        )

    def validate_identity(self, id_token: str, access_token: str) -> GoogleIdentity:
        if not id_token or not access_token:
            raise GoogleOAuthError("Google identity validation requires tokens")
        try:
            response = httpx.get(GOOGLE_TOKENINFO_ENDPOINT, params={"id_token": id_token}, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise GoogleOAuthError("Google identity validation failed") from exc

        audience = data.get("aud")
        if audience != self._settings.google_oauth_client_id:
            raise GoogleOAuthError("Google identity audience did not match this app")
        subject = data.get("sub")
        if not subject:
            raise GoogleOAuthError("Google identity response was missing subject")
        return GoogleIdentity(
            subject=subject,
            email=data.get("email"),
            email_verified=str(data.get("email_verified")).lower() == "true",
            name=data.get("name"),
            avatar_url=data.get("picture"),
        )

