import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from backend.app.auth.crypto import encrypt_refresh_token
from backend.app.auth.scopes import missing_required_scopes
from backend.app.auth.security import hash_secret
from backend.app.providers.google_oauth import GoogleIdentity
from backend.app.store.database import db_session
from backend.app.store.models import OAuthStateModel, OAuthTokenModel, ServerSessionModel, UserModel

OAUTH_PROVIDER_GOOGLE = "google"
CONNECTION_CONNECTED = "connected"
CONNECTION_INCOMPLETE_SCOPES = "incomplete_scopes"
CONNECTION_RECONNECT_REQUIRED = "reconnect_required"
CONNECTION_DISCONNECTED = "disconnected"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _user_to_dict(row: UserModel) -> dict:
    return {
        "id": row.id,
        "google_sub": row.google_sub,
        "email": row.email,
        "email_verified": row.email_verified,
        "name": row.name,
        "avatar_url": row.avatar_url,
    }


def _oauth_token_to_dict(row: OAuthTokenModel | None) -> dict | None:
    if row is None:
        return None
    return {
        "id": row.id,
        "user_id": row.user_id,
        "provider": row.provider,
        "encrypted_refresh_token": row.encrypted_refresh_token,
        "granted_scopes": row.granted_scopes or [],
        "missing_scopes": row.missing_scopes or [],
        "connection_status": row.connection_status,
        "reconnect_required": row.reconnect_required,
        "last_verified_at": row.last_verified_at.isoformat() if row.last_verified_at else None,
    }


def create_oauth_state(state: str, code_verifier: str, redirect_uri: str, expires_at: datetime) -> None:
    with db_session() as db:
        db.add(
            OAuthStateModel(
                state_hash=hash_secret(state),
                code_verifier=code_verifier,
                redirect_uri=redirect_uri,
                expires_at=expires_at,
            )
        )


def consume_oauth_state(state: str, now: datetime | None = None) -> dict | None:
    current_time = _aware(now or utc_now())
    state_hash = hash_secret(state)
    with db_session() as db:
        row = db.get(OAuthStateModel, state_hash)
        if row is None or row.consumed_at is not None or _aware(row.expires_at) < current_time:
            return None
        row.consumed_at = current_time
        return {
            "state_hash": row.state_hash,
            "code_verifier": row.code_verifier,
            "redirect_uri": row.redirect_uri,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        }


def upsert_user_from_google(identity: GoogleIdentity) -> dict:
    with db_session() as db:
        row = db.scalar(select(UserModel).where(UserModel.google_sub == identity.subject))
        if row is None:
            row = UserModel(
                id=str(uuid.uuid4()),
                google_sub=identity.subject,
                email=identity.email,
                email_verified=identity.email_verified,
                name=identity.name,
                avatar_url=identity.avatar_url,
            )
            db.add(row)
            db.flush()
            return _user_to_dict(row)

        row.email = identity.email
        row.email_verified = identity.email_verified
        row.name = identity.name
        row.avatar_url = identity.avatar_url
        return _user_to_dict(row)


def _connection_status(granted_scopes: list[str], has_refresh_token: bool) -> tuple[str, list[str], bool]:
    missing_scopes = missing_required_scopes(granted_scopes)
    if missing_scopes:
        return CONNECTION_INCOMPLETE_SCOPES, missing_scopes, True
    if not has_refresh_token:
        return CONNECTION_RECONNECT_REQUIRED, [], True
    return CONNECTION_CONNECTED, [], False


def upsert_google_oauth_token(
    user_id: str,
    granted_scopes: list[str],
    refresh_token: str | None,
    verified_at: datetime | None = None,
) -> dict:
    normalized_grants = sorted(set(granted_scopes))
    with db_session() as db:
        row = db.scalar(
            select(OAuthTokenModel).where(
                OAuthTokenModel.user_id == user_id,
                OAuthTokenModel.provider == OAUTH_PROVIDER_GOOGLE,
            )
        )
        if row is None:
            row = OAuthTokenModel(user_id=user_id, provider=OAUTH_PROVIDER_GOOGLE)
            db.add(row)

        if refresh_token:
            row.encrypted_refresh_token = encrypt_refresh_token(refresh_token)
        status, missing_scopes, reconnect_required = _connection_status(
            normalized_grants,
            bool(row.encrypted_refresh_token),
        )
        row.granted_scopes = normalized_grants
        row.missing_scopes = missing_scopes
        row.connection_status = status
        row.reconnect_required = reconnect_required
        row.last_verified_at = verified_at or utc_now()
        db.flush()
        return _oauth_token_to_dict(row) or {}


def get_google_oauth_token(user_id: str) -> dict | None:
    with db_session() as db:
        row = db.scalar(
            select(OAuthTokenModel).where(
                OAuthTokenModel.user_id == user_id,
                OAuthTokenModel.provider == OAUTH_PROVIDER_GOOGLE,
            )
        )
        return _oauth_token_to_dict(row)


def create_server_session(
    user_id: str,
    session_token: str,
    csrf_token: str,
    expires_at: datetime,
) -> dict:
    with db_session() as db:
        row = ServerSessionModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_token_hash=hash_secret(session_token),
            csrf_token_hash=hash_secret(csrf_token),
            expires_at=expires_at,
        )
        db.add(row)
        db.flush()
        return {
            "id": row.id,
            "user_id": row.user_id,
            "csrf_token_hash": row.csrf_token_hash,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        }


def get_session_context(session_token: str | None, now: datetime | None = None) -> dict | None:
    if not session_token:
        return None
    current_time = _aware(now or utc_now())
    with db_session() as db:
        session_row = db.scalar(
            select(ServerSessionModel).where(ServerSessionModel.session_token_hash == hash_secret(session_token))
        )
        if (
            session_row is None
            or session_row.revoked_at is not None
            or _aware(session_row.expires_at) < current_time
        ):
            return None
        user = db.get(UserModel, session_row.user_id)
        if user is None:
            return None
        session_row.last_seen_at = current_time
        token = db.scalar(
            select(OAuthTokenModel).where(
                OAuthTokenModel.user_id == user.id,
                OAuthTokenModel.provider == OAUTH_PROVIDER_GOOGLE,
            )
        )
        return {
            "session": {
                "id": session_row.id,
                "user_id": session_row.user_id,
                "csrf_token_hash": session_row.csrf_token_hash,
            },
            "user": _user_to_dict(user),
            "oauth_token": _oauth_token_to_dict(token),
        }


def revoke_server_session(session_token: str | None) -> bool:
    if not session_token:
        return False
    with db_session() as db:
        row = db.scalar(
            select(ServerSessionModel).where(ServerSessionModel.session_token_hash == hash_secret(session_token))
        )
        if row is None or row.revoked_at is not None:
            return False
        row.revoked_at = utc_now()
        return True
