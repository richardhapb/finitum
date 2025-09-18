from collections.abc import Generator
from datetime import datetime
import pytz
import email
import os
from imaplib import IMAP4_SSL
from typing import cast
from dotenv import load_dotenv
from contextlib import contextmanager
from dataclasses import dataclass
from utils import get_logger

from bs4 import BeautifulSoup

TZ = pytz.timezone("America/Santiago")
logger = get_logger()


def remove_html_tags_beautifulsoup(html_doc: str):
    soup = BeautifulSoup(html_doc, "html.parser")
    return " ".join(soup.get_text().strip().split())


class AuthenticacionError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass
class Message:
    remitent: str
    subject: str
    date: datetime
    body: str

    def __str__(self) -> str:
        output = ""
        output += f"From: {self.remitent}\n"
        output += f"Subject: {self.subject}\n"
        output += f"Date: {self.date}\n\n"
        output += f"{self.body}"

        return output

    @staticmethod
    def parse_message(raw_email: bytes, date_from: datetime | None = None) -> "Message | None":
        # Parse the raw email data
        msg = email.message_from_bytes(raw_email)

        # Accessing headers
        remitent = _ensure_str(msg["from"])
        subject = _ensure_str(msg["subject"])
        dt = msg["date"]

        try:
            # Try standard format with weekday
            date = datetime.strptime(dt.split(" (")[0], "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            try:
                # Try alternative format without weekday
                date = datetime.strptime(dt, "%d %b %Y %H:%M:%S %z")
            except ValueError:
                logger.exception("Error parsing date (got %r). Falling back to now().", dt)
                date = datetime.now(TZ)

        if date_from and date.date() < date_from.date():
            logger.info(
                "Skipping message, the date is before from the threshold, expected since: %s, message date: %s",
                date_from.date(),
                date.date(),
            )
            return None

        content = ""
        # Accessing the body
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdisposition = part.get("Content-Disposition")

                # Extract plain text or HTML body
                if ctype == "text/plain" and cdisposition is None:
                    content += _ensure_str(bytes(part.get_payload(decode=True)))
                elif ctype == "text/html" and cdisposition is None:
                    html_body = _ensure_str(bytes(part.get_payload(decode=True)))
                    content += remove_html_tags_beautifulsoup(html_body)
                # Handle attachments if needed
                elif cdisposition and "attachment" in cdisposition:
                    filename = part.get_filename()
                    if filename:
                        # Save attachment or process it
                        content += f"\nAttachment: {filename}"
        else:
            # Single part message
            html_body = _ensure_str(bytes(msg.get_payload(decode=True)))
            content += remove_html_tags_beautifulsoup(html_body)

        message = Message(remitent, subject, date, content)

        return message


class EmailManager:
    def __init__(self):
        self.conn: IMAP4_SSL = IMAP4_SSL("imap.gmail.com", 993)
        self._logged: bool = False
        load_dotenv()

    @contextmanager
    def login(self) -> Generator[None]:
        if self._logged:
            return

        user: str = os.getenv("GMAIL_USER", "")
        password: str = os.getenv("GMAIL_PASS", "")

        if not user or not password:
            msg = f"User/Password missed, user: {user}, password: {password}"
            raise AuthenticacionError(msg)

        try:
            self.conn.login(user, password)
        except IMAP4_SSL.error:
            raise AuthenticacionError

        yield

        self.conn.logout()

    def get_messages(self, date_from: datetime | None = None) -> list[Message]:
        with self.login():
            messages: list[Message] = []

            self.conn.select("Transactions")

            _, data = self.conn.search(None, "UNSEEN")
            msgs = data[0].split()

            n: int = len(msgs)

            for i, num in enumerate(msgs):
                _, dat = self.conn.fetch(num, "(RFC822)")
                if dat and dat[0]:
                    logger.info("Processing message %d of %d", i + 1, n)
                    parsed = Message.parse_message(cast(bytes, dat[0][1]), date_from)
                    if parsed:
                        messages.append(parsed)

            return messages


def _ensure_str(s: bytes | bytearray | str) -> str:
    return bytes(s).decode("utf-8", errors="replace") if isinstance(s, (bytes, bytearray)) else s

if __name__ == "__main__":
    em: EmailManager = EmailManager()
    em.get_messages()
