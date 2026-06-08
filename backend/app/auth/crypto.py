import base64
import hashlib

from cryptography.fernet import Fernet

from backend.app.core.config import get_settings


class TokenEncryptionError(RuntimeError):
    pass


def _fernet() -> Fernet:
    secret = get_settings().token_encryption_key.strip()
    if not secret:
        raise TokenEncryptionError("TOKEN_ENCRYPTION_KEY or OAUTH_TOKEN_ENCRYPTION_KEY is not configured")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_refresh_token(refresh_token: str) -> str:
    if not refresh_token:
        raise TokenEncryptionError("Refresh token is empty")
    return _fernet().encrypt(refresh_token.encode("utf-8")).decode("utf-8")


def decrypt_refresh_token(encrypted_refresh_token: str) -> str:
    if not encrypted_refresh_token:
        raise TokenEncryptionError("Encrypted refresh token is empty")
    return _fernet().decrypt(encrypted_refresh_token.encode("utf-8")).decode("utf-8")
