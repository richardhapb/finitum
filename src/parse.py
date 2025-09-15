import re
import pytz
from datetime import datetime
from enum import Enum

import utils

logger = utils.get_logger()

TZ = pytz.timezone("America/Santiago")


class Currency(Enum):
    USD = "usd"
    CLP = "clp"


class ExpenseCategory(Enum):
    GENERAL = "general"
    ONLINE_PLATFORM = "online_platform"


class Transaction:
    currency: Currency
    value: float
    category: ExpenseCategory
    date: datetime

    AMOUNT_REGEX = r"compra por (\S+)"

    def _parse_amount(self, amount_str: str) -> None:
        if not amount_str:
            self.currency = Currency.CLP
            self.value = 0.0
            return

        if amount_str.startswith("US"):
            self.currency = Currency.USD
            amount_str = amount_str.strip("US")
        else:
            self.currency = Currency.CLP

        try:
            self.value = float(amount_str.strip("$").replace(".", "").replace(",", "."))
        except ValueError:
            logger.exception("Error parsing amount")
            self.value = 0.0

    # Amount

    @classmethod
    def _get_amount_str(cls, content: str) -> str:
        amounts = re.findall(cls.AMOUNT_REGEX, content)
        amount = amounts[0] if amounts else ""
        return amount

    @staticmethod
    def _get_category(commerce_str: str) -> ExpenseCategory:
        if commerce_str in ["Upwork"]:
            return ExpenseCategory.ONLINE_PLATFORM
        return ExpenseCategory.GENERAL


class Expense(Transaction):
    commerce: str

    # REGEX
    COMPRA_GIRO = r"compra|giro en Cajero"
    AMOUNT_REGEX = rf"(?:{COMPRA_GIRO}) por (\S+)"
    COMMERCE_REGEX = r"compra por \S+ con \D+\d+ en (\D+)?"
    DATE_REGEX = (
        rf"(?:{COMPRA_GIRO}) por \S+ con \D+.* (?:en \D+)? .* el (\d+\d+/\d+/\d+\s+\d+:\d+)"
    )

    def __init__(self, amount_str: str, commerce_str: str, date_str: str):
        self._parse_amount(amount_str)
        self.commerce = self._sanitize_commerce_str(commerce_str)
        self.category = self._get_category(self.commerce)
        try:
            self.date = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
        except ValueError:
            logger.exception("Error parsing date")
            self.date = datetime.now()

    @classmethod
    def get_expense(cls, content: str) -> "Expense":
        amount_str = cls._get_amount_str(content)
        commerce_str = cls._get_commerce_str(content)
        date_str = cls._get_date_str(content)

        return Expense(amount_str, commerce_str, date_str)

    # Commerce / Category

    @classmethod
    def _get_commerce_str(cls, content: str) -> str:
        commerces = re.findall(cls.COMMERCE_REGEX, content)
        commerce = commerces[0] if commerces else ""
        return commerce

    @staticmethod
    def _sanitize_commerce_str(commerce_str: str) -> str:
        return commerce_str.strip("").strip("-").strip()

    # Date

    @classmethod
    def _get_date_str(cls, content: str) -> str:
        dates = re.findall(cls.DATE_REGEX, content)
        date = dates[0] if dates else ""
        return date


class Transference(Transaction):
    recipient: str

    AMOUNT_REGEX = r"Monto\s*(\S+)"
    RECIPIENT_REGEX = r"(?:Nombre y Apellido |Nombre )(.*) Rut"

    def __init__(self, amount_str: str, recipient_str: str, date_str: str):
        self._parse_amount(amount_str)
        self.recipient = recipient_str
        self.category = self._get_category(self.recipient)
        try:
            self.date = datetime.fromisoformat(date_str).astimezone(TZ)
        except ValueError:
            logger.exception("Error parsing date")
            self.date = datetime.now()

    @classmethod
    def get_transference(cls, content: str, date_str: str) -> "Transference":
        amount_str = cls._get_amount_str(content)
        commerce_str = cls._get_recipient_str(content)

        return Transference(amount_str, commerce_str, date_str)

    # Commerce / Category

    @classmethod
    def _get_recipient_str(cls, content: str) -> str:
        recipients = re.findall(cls.RECIPIENT_REGEX, content)
        recipient = recipients[0] if recipients else ""
        return recipient
