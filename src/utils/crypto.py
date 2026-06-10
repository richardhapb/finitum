"""Symmetric encryption helpers for sensitive credential fields.

Keyed by the ``CREDENTIALS_ENCRYPTION_KEY`` environment variable (a urlsafe
base64-encoded 32-byte Fernet key). Fails fast at import time if missing or
invalid, mirroring the ``SECRET_KEY`` guard in ``src/api/jwt.py``.

Generate a key with::

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from cryptography.fernet import Fernet, InvalidToken

from utils.config import CREDENTIALS_ENCRYPTION_KEY
from utils.logger import get_logger

logger = get_logger()


class CryptoError(Exception):
    pass


if not CREDENTIALS_ENCRYPTION_KEY:
    raise CryptoError("Missing CREDENTIALS_ENCRYPTION_KEY")

try:
    _fernet = Fernet(CREDENTIALS_ENCRYPTION_KEY.encode())
except (ValueError, TypeError) as exc:
    raise CryptoError("Invalid CREDENTIALS_ENCRYPTION_KEY") from exc


def encrypt(value: str | None) -> str | None:
    """Encrypt a plaintext string. ``None`` passes through unchanged."""
    if value is None:
        return None
    return _fernet.encrypt(value.encode()).decode()


def decrypt(value: str | None) -> str | None:
    """Decrypt a ciphertext string produced by :func:`encrypt`.

    ``None`` passes through unchanged. If the value is not valid ciphertext
    (e.g. legacy plaintext), it is returned as-is so reads degrade gracefully.
    """
    if value is None:
        return None
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        logger.warning("Failed to decrypt credential value; returning raw value")
        return value
