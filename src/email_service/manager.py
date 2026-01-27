from __future__ import annotations

import base64
import email
from dataclasses import dataclass
from datetime import UTC, datetime
from email.header import decode_header
from email.message import Message as EmailMessage
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource, build

from utils.config import TZ
from utils.logger import get_logger

logger = get_logger()

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials


def _ensure_str(s: bytes | bytearray | str | EmailMessage | None) -> str:
    if s is None:
        return ""
    if isinstance(s, EmailMessage):
        return str(s)

    return bytes(s).decode("utf-8", errors="replace") if isinstance(s, (bytes, bytearray)) else s


def _decode_header(header_value: str | None) -> str:
    """Decode MIME-encoded header (RFC 2047) like =?utf-8?q?...?= to plain text."""
    if not header_value:
        return ""
    parts = decode_header(header_value)
    decoded_parts = []
    for content, charset in parts:
        if isinstance(content, bytes):
            decoded_parts.append(content.decode(charset or "utf-8", errors="replace"))
        else:
            decoded_parts.append(content)
    return "".join(decoded_parts)


def _b64url_decode(s: str) -> bytes:
    # Gmail "raw" is base64url without padding
    padding = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)


def remove_html_tags(html_doc: str) -> str:
    soup = BeautifulSoup(html_doc, "html.parser")
    return soup.get_text()


def _parse_date(header_value: str | None) -> datetime:
    """Robust RFC2822 date parsing -> tz-aware UTC then convert to TZ."""
    if not header_value:
        # Fallback: now (tz-aware)
        return datetime.now(UTC).astimezone(TZ)
    try:
        dt = parsedate_to_datetime(header_value)  # returns aware or naive
    except Exception:
        dt = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(TZ)


def normalize_date_from(date_from: datetime | None) -> datetime | None:
    if date_from is None:
        return None
    if date_from.tzinfo is None:
        # Assume local TZ if naive
        date_from = TZ.localize(date_from)
    return date_from.astimezone(TZ)


def _pick_body(msg: EmailMessage) -> str:  # noqa: C901
    """Prefer text/plain (inline/none), else text/html stripped; fallback to join."""
    texts: list[str] = []
    htmls: list[str] = []

    def handle_payload(payload: str, ctype: str) -> None:
        if not payload:
            return

        if ctype == "text/plain":
            texts.append(payload)
        elif ctype == "text/html":
            htmls.append(remove_html_tags(payload))

    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart():
                continue  # skip multipart containers

            disp = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disp:
                continue  # skip attachments

            ctype = part.get_content_type()
            payload = _ensure_str(part.get_payload(decode=True))

            handle_payload(payload, ctype)
    else:
        ctype = msg.get_content_type()
        payload = _ensure_str(msg.get_payload(decode=True))

        handle_payload(payload, ctype)

    if texts:
        return "\n".join(t.strip() for t in texts if t.strip())
    if htmls:
        return "\n".join(h.strip() for h in htmls if h.strip())
    return ""  # nothing usable


@dataclass
class Message:
    remitent: str
    subject: str
    date: datetime
    body: str

    def __str__(self) -> str:
        return f"From: {self.remitent}\nSubject: {self.subject}\nDate: {self.date}\n\n{self.body}"

    @classmethod
    def parse_message(cls, raw_email_b64url: str, date_from: datetime | None = None) -> Message | None:
        # Decode base64url -> bytes -> EmailMessage
        raw_bytes = _b64url_decode(raw_email_b64url)
        msg: EmailMessage = email.message_from_bytes(raw_bytes)

        remitent = _decode_header(msg.get("from"))
        subject = _decode_header(msg.get("subject"))
        date = _parse_date(_ensure_str(msg.get("date")))

        df = normalize_date_from(date_from)
        if df and not cls._is_after_date_from(date, df):
            return None

        body = _pick_body(msg)
        return Message(remitent=remitent, subject=subject, date=date, body=body)

    @staticmethod
    def _is_after_date_from(date: datetime, date_from: datetime) -> bool:
        # is earlier than threshold?
        return date > date_from


class EmailManager:
    def __init__(self, credentials: Credentials):
        self.creds: Credentials = credentials
        self.service: Resource = self.login()

        assert "users" in self.service.__dict__

    def login(self) -> Resource:
        return build("gmail", "v1", credentials=self.creds)

    def search_messages(self, query: str) -> list[dict[str, int | str]]:
        """Perform the query and traverse all the messages of the response"""
        try:
            # API call
            result = self.service.users().messages().list(userId="me", q=query).execute()  # type: ignore
        except RefreshError:
            logger.exception("Google OAuth refresh failed; re-consent required")
            raise

        messages = []
        if "messages" in result:
            messages.extend(result["messages"])
        while "nextPageToken" in result:
            page_token = result["nextPageToken"]
            result = self.service.users().messages().list(userId="me", q=query, pageToken=page_token).execute()  # type: ignore
            if "messages" in result:
                messages.extend(result["messages"])
        return messages

    def get_messages(self, query: str, date_from: datetime | None = None) -> list[Message]:
        """
        Traverse all the messages from the user and parse them, filter according
        to the received query and form the date if it is passed, otherwise get the latest
        update for the user.
        """

        messages: list[Message] = []
        msgs = self.search_messages(query)
        n = len(msgs)
        logger.info("%d messages received", n)
        for i, msg in enumerate(msgs):
            logger.debug("Processing %d/%d", i, n)

            r = self.service.users().messages().get(userId="me", id=msg["id"], format="raw").execute()  # type: ignore
            parsed = Message.parse_message(r["raw"], date_from)
            if parsed:
                messages.append(parsed)

        logger.info("Returning %d messages", len(messages))
        return messages


if __name__ == "__main__":
    from tasks.email_fetch import get_messages

    get_messages()
    logger.info("Get messages task triggered")
