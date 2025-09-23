import re
import typing
from datetime import datetime
from sqlmodel import Session
from parsers.base import Transaction

from email_service.manager import Message
from utils.logger import get_logger

if typing.TYPE_CHECKING:
    from db.models import Transference as DBTransference

logger = get_logger()


class Transference(Transaction):
    recipient: str

    AMOUNT_REGEX = r"Monto\s*(\S+)\s*(?:Mensaje|ID)"
    RECIPIENT_REGEX = r"(?:Nombre y Apellido |Nombre )(.*) Rut"

    def __init__(self, amount_str: str, recipient_str: str, date: datetime):
        self._parse_amount(amount_str)
        self.recipient = recipient_str.strip()
        self.category = self._get_category(self.recipient)
        self.date = date

    @classmethod
    def get_transference(cls, msg: Message) -> "Transference":
        amount_str = cls._get_amount_str(msg.body)
        recipient_str = cls._get_recipient_str(msg.body)
        return Transference(amount_str, recipient_str, msg.date)

    # Commerce / Category

    @classmethod
    def _get_recipient_str(cls, content: str) -> str:
        recipients = re.findall(cls.RECIPIENT_REGEX, content)
        recipient = recipients[0] if recipients else ""
        return recipient

    def to_db_model(self) -> "DBTransference":
        """Convert to database model"""
        from db.models import Transference as DBTransference

        return DBTransference(
            recipient=self.recipient,
            amount=self.value,
            currency=self.currency,
            category=self.category,
            date=self.date,
            description="Extracted from email",
        )


def save_extracted_transference(msg: Message, session: Session) -> "DBTransference":
    """Extract transference from text content and save to database"""
    transference_parser = Transference.get_transference(msg)
    db_transference = transference_parser.to_db_model()
    session.add(db_transference)
    session.commit()
    session.refresh(db_transference)
    return db_transference
