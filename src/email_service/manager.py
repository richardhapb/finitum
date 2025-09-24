from datetime import datetime
from google.oauth2.credentials import Credentials
import pytz
import email
from googleapiclient.discovery import Resource, build
from imaplib import IMAP4_SSL
from typing import cast
from dataclasses import dataclass
from utils.logger import get_logger

from bs4 import BeautifulSoup
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import User, UserGoogleCredential, rebuild_credentials

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
    def __init__(self, user: "User", credentials: Credentials):
        self.conn: IMAP4_SSL = IMAP4_SSL("imap.gmail.com", 993)
        self.user: "User" = user
        self.creds: Credentials = credentials
        self.service: Resource = self.login()

    def search_messages(self, query: str) -> list[dict[str, int | str]]:
        if not self.service:
            self.login()

        result = self.service.users().messages().list(userId='me',q=query).execute()
        messages = []

        if 'messages' in result:
            messages.extend(result['messages'])
        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = self.service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
            if 'messages' in result:
                messages.extend(result['messages'])
        return messages

    def login(self) -> Resource:
        return build("gmail", "v1", credentials=self.creds)

    def get_messages(self, query: str, date_from: datetime | None = None) -> list[Message]:
        messages: list[Message] = []

        msgs = self.search_messages(query)

        n: int = len(msgs)

        for i, msg in enumerate(msgs):
            msg_bytest = self.service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            logger.info("Processing message %d of %d", i + 1, n)
            parsed = Message.parse_message(cast(bytes, msg_bytest), date_from)
            if parsed:
                messages.append(parsed)

        return messages


def _ensure_str(s: bytes | bytearray | str) -> str:
    return bytes(s).decode("utf-8", errors="replace") if isinstance(s, (bytes, bytearray)) else s

if __name__ == "__main__":
    from models import User, UserGoogleCredential, rebuild_credentials
    from database import get_session
    with next(get_session()) as session:
        user = session.get(User, {"username": "richardhapb"})
        credentials_obj = session.get(UserGoogleCredential, {"user": user}) if user else None
        if user and credentials_obj:
            credentials = rebuild_credentials(credentials_obj)
            em: EmailManager = EmailManager(user, credentials)
            em.get_messages("is:unread")
        else:
            logger.error("Missed user/credentials, user=%s, credentials=%s", user, credentials_obj)
