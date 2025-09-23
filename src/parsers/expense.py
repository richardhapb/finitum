import re
import typing
from datetime import datetime
from sqlmodel import Session
from parsers.base import Transaction

from email_service.manager import Message
from utils.logger import get_logger

if typing.TYPE_CHECKING:
    from db.models import Expense as DBExpense

logger = get_logger()


class Expense(Transaction):
    commerce: str

    # REGEX
    COMPRA_GIRO = r"compra|giro en Cajero"
    AMOUNT_REGEX = rf"(?:{COMPRA_GIRO})\s*por\s*(\S+)"
    DATE_REGEX = r"\d{1,2}/\d{1,2}/\d{4}(?:\s+\d{1,2}:\d{2})?"
    COMMERCE_REGEX = rf"compra\s+por\s+\S+\s*con\s*\D+\d+\s*en\s*(.+)\s*el\s*{DATE_REGEX}"

    def __init__(self, amount_str: str, commerce_str: str, date: datetime):
        self._parse_amount(amount_str)
        self.commerce = self._sanitize_commerce_str(commerce_str)
        self.category = self._get_category(self.commerce)
        self.date = date

    @classmethod
    def get_expense(cls, msg: Message) -> "Expense":
        amount_str = cls._get_amount_str(msg.body)
        if "giro" in msg.subject.lower():
            commerce_str = "GIRO EN CAJERO"
        else:
            commerce_str = cls._get_commerce_str(msg.body)
        return Expense(amount_str, commerce_str, msg.date)

    # Commerce / Category

    @classmethod
    def _get_commerce_str(cls, content: str) -> str:
        commerces = re.findall(cls.COMMERCE_REGEX, content)
        commerce = commerces[0] if commerces else ""
        return commerce

    @staticmethod
    def _sanitize_commerce_str(commerce_str: str) -> str:
        # Clean and keep original casing for storage, but category matching uses normalized text
        return commerce_str.strip().strip("-").strip()

    def to_db_model(self) -> "DBExpense":
        """Convert to database model"""
        from db.models import Expense as DBExpense

        return DBExpense(
            commerce=self.commerce,
            amount=self.value,
            currency=self.currency,
            category=self.category,
            date=self.date,
            description="Extracted from email",
        )


def save_extracted_expense(msg: Message, session: Session) -> "DBExpense":
    """Extract expense from text content and save to database"""
    expense_parser = Expense.get_expense(msg)
    db_expense = expense_parser.to_db_model()
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense
