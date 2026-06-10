"""Inbound forwarding ingestion (Phase 2).

Replaces Gmail API polling with inbound email forwarding. A Cloudflare Email
Routing worker POSTs the raw MIME of each forwarded message to
``POST /ingest/email``; this module turns that raw MIME into a persisted
expense/transference through the existing parser pipeline.

The flow per inbound message:

1. Resolve the user from the recipient address ``u-<token>@in.<domain>``.
2. Detect Gmail forwarding-confirmation mails and stash the link/code in Redis
   so the frontend can offer near one-click setup.
3. Dedupe on (user_id, Message-ID) via Redis to ignore re-forwards.
4. Feed the raw MIME through ``Message`` parsing and ``save_expense``. The
   parser enforces the per-bank sender allowlist (``remitents`` in
   ``regex.json``), so spoofed/unrelated senders are dropped here.
"""

from __future__ import annotations

import email
import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from email_service.manager import Message, _decode_header, remove_html_tags
from parsers.parser import BankNotFoundError, EmailParser, save_expense
from utils.logger import get_logger

if TYPE_CHECKING:
    from email.message import Message as EmailMessage

    from redis import Redis
    from sqlmodel import Session

    import db.models as md


logger = get_logger()

# Gmail sends the forwarding confirmation from this address.
FORWARDING_CONFIRMATION_SENDER = "forwarding-noreply@google.com"

# Redis key namespaces / TTLs.
_DEDUPE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days
_CONFIRMATION_TTL_SECONDS = 60 * 60  # 1 hour
_LAST_EMAIL_TTL_SECONDS = 90 * 24 * 60 * 60  # 90 days (status display)

_RECIPIENT_RE = re.compile(r"u-([a-z0-9_-]+)@", re.IGNORECASE)
_CONFIRM_URL_RE = re.compile(r"https://mail\.google\.com/mail/\S*?(?:vf-|ik=)\S+", re.IGNORECASE)
_CONFIRM_CODE_RE = re.compile(r"confirmation code\D*(\d{6,})", re.IGNORECASE)


class IngestOutcome(Enum):
    SAVED = "saved"
    DUPLICATE = "duplicate"
    CONFIRMATION = "confirmation"
    IGNORED = "ignored"
    UNKNOWN_TOKEN = "unknown_token"  # noqa: S105 - status string, not a secret


@dataclass
class IngestResult:
    outcome: IngestOutcome
    detail: str | None = None


def verify_signature(secret: str, body: bytes, signature: str | None) -> bool:
    """Constant-time check of ``X-Finitum-Signature`` (HMAC-SHA256 hex of body).

    Accepts an optional ``sha256=`` prefix to match the GitHub-style convention.
    """
    if not secret or not signature:
        return False
    provided = signature.split("=", 1)[1] if signature.startswith("sha256=") else signature
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided.strip())


def extract_token_from_recipient(recipient: str | None) -> str | None:
    """Pull ``<token>`` out of ``u-<token>@in.<domain>`` (case-insensitive)."""
    if not recipient:
        return None
    match = _RECIPIENT_RE.search(recipient)
    return match.group(1).lower() if match else None


def build_ingest_address(token: str, domain: str) -> str:
    """Build the ingest address. ``domain`` is the full mail domain that receives
    forwarded mail — e.g. ``finitum.app`` with Cloudflare Email Routing on the
    apex (recommended), or ``in.finitum.app`` for a dedicated subdomain."""
    return f"u-{token}@{domain}"


def _is_forwarding_confirmation(email_msg: EmailMessage) -> bool:
    sender = _decode_header(email_msg.get("from")).lower()
    return FORWARDING_CONFIRMATION_SENDER in sender


def _message_body_text(email_msg: EmailMessage) -> str:
    """Best-effort full-text body (plain + html stripped) for link extraction."""
    chunks: list[str] = []
    parts = email_msg.walk() if email_msg.is_multipart() else [email_msg]
    for part in parts:
        if part.is_multipart():
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        text = payload.decode("utf-8", errors="replace") if isinstance(payload, (bytes, bytearray)) else str(payload)
        chunks.append(remove_html_tags(text) if part.get_content_type() == "text/html" else text)
    return "\n".join(chunks)


def extract_confirmation(email_msg: EmailMessage) -> dict[str, str] | None:
    """Extract the Gmail forwarding confirmation link and/or code."""
    text = _message_body_text(email_msg)
    url_match = _CONFIRM_URL_RE.search(text)
    code_match = _CONFIRM_CODE_RE.search(text)
    if not url_match and not code_match:
        return None
    result: dict[str, str] = {}
    if url_match:
        result["url"] = url_match.group(0)
    if code_match:
        result["code"] = code_match.group(1)
    return result


def _dedupe_key(user_id: int, message_id: str) -> str:
    digest = hashlib.sha256(message_id.encode("utf-8")).hexdigest()
    return f"ingest:dedupe:{user_id}:{digest}"


def confirmation_key(token: str) -> str:
    return f"ingest:confirmation:{token}"


def last_email_key(user_id: int) -> str:
    return f"ingest:last_email:{user_id}"


def _mark_last_email(redis_client: Redis, user_id: int) -> None:
    try:
        redis_client.setex(last_email_key(user_id), _LAST_EMAIL_TTL_SECONDS, datetime.now(UTC).isoformat())
    except Exception:
        logger.warning("Failed to record last-email timestamp for user %s", user_id)


def get_last_email_at(redis_client: Redis, user_id: int) -> str | None:
    try:
        raw = redis_client.get(last_email_key(user_id))
    except Exception:
        return None
    if raw is None:
        return None
    return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)


def get_confirmation(redis_client: Redis, token: str) -> dict[str, str] | None:
    import json

    try:
        raw = redis_client.get(confirmation_key(token))
    except Exception:
        return None
    if raw is None:
        return None
    raw_str = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    try:
        value = json.loads(raw_str)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def process_inbound_email(
    raw_bytes: bytes,
    recipient: str | None,
    *,
    session: Session,
    redis_client: Redis,
) -> IngestResult:
    """Process one forwarded MIME message end-to-end.

    Returns an :class:`IngestResult`; callers should always return HTTP 200 to
    the worker (even on UNKNOWN_TOKEN) to avoid retries leaking token validity.
    """
    import json

    import sqlmodel

    import db.models as md

    token = extract_token_from_recipient(recipient)
    if not token:
        logger.warning("Inbound email with unparseable recipient: %r", recipient)
        return IngestResult(IngestOutcome.UNKNOWN_TOKEN, "unparseable recipient")

    user = session.exec(sqlmodel.select(md.User).where(md.User.ingest_token == token)).first()

    email_msg = email.message_from_bytes(raw_bytes)

    # Gmail forwarding confirmation: stash for the frontend even before a user
    # exists/owns the token (token is the only identifier we have here).
    if _is_forwarding_confirmation(email_msg):
        confirmation = extract_confirmation(email_msg)
        if confirmation:
            try:
                redis_client.setex(confirmation_key(token), _CONFIRMATION_TTL_SECONDS, json.dumps(confirmation))
            except Exception:
                logger.exception("Failed to store forwarding confirmation for token %s", token)
        logger.info("Captured forwarding confirmation for token %s", token)
        return IngestResult(IngestOutcome.CONFIRMATION)

    if user is None or user.id is None:
        logger.warning("Inbound email for unknown ingest token (len=%d)", len(token))
        return IngestResult(IngestOutcome.UNKNOWN_TOKEN, "unknown token")

    # Dedupe on Message-ID.
    message_id = (email_msg.get("Message-ID") or email_msg.get("Message-Id") or "").strip()
    if message_id:
        key = _dedupe_key(user.id, message_id)
        try:
            if not redis_client.set(key, "1", nx=True, ex=_DEDUPE_TTL_SECONDS):
                logger.info("Dropping duplicate inbound email for user %s (%s)", user.id, message_id)
                return IngestResult(IngestOutcome.DUPLICATE)
        except Exception:
            logger.warning("Dedupe check failed for user %s; proceeding", user.id)

    _mark_last_email(redis_client, user.id)
    return _parse_and_save(user, email_msg, session)


def _parse_and_save(user: md.User, email_msg: EmailMessage, session: Session) -> IngestResult:
    """Run the existing parser pipeline over a forwarded message and persist it."""
    parsed = Message.from_email_message(email_msg)
    if parsed is None:
        return IngestResult(IngestOutcome.IGNORED, "unparseable message")

    parser = EmailParser(user.bank, user.email)
    try:
        parser.build_parser()
    except BankNotFoundError:
        logger.exception("Cannot build parser for bank %s", user.bank)
        return IngestResult(IngestOutcome.IGNORED, "unknown bank")

    saved = save_expense(user.id, parser, parsed, session)
    if saved is None:
        logger.info("Inbound email for user %s did not match an expense (sender=%s)", user.id, parsed.remitent)
        return IngestResult(IngestOutcome.IGNORED, "not an expense")

    logger.info("Saved inbound expense/transference for user %s", user.id)
    return IngestResult(IngestOutcome.SAVED)
