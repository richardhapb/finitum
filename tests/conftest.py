"""Shared test configuration.

Set the secrets that import-time guards (``utils.crypto``, ``api.jwt``) and the
forwarding webhook require, *before* any module reads them via ``utils.config``.
``setdefault`` so a real environment (local/CI override) still wins.
"""

import os

from cryptography.fernet import Fernet

# Generate an ephemeral Fernet key per test run rather than committing a
# key-shaped literal (avoids secret-scanner noise and accidental reuse).
os.environ.setdefault("CREDENTIALS_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("INGEST_WEBHOOK_SECRET", "test-ingest-secret")
os.environ.setdefault("INGEST_DOMAIN", "finitum.app")
