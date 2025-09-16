import json
import re
import typing
import pytz
import unicodedata
from datetime import datetime
from enum import Enum
from sqlmodel import Session

import utils

if typing.TYPE_CHECKING:
    from models import Expense as DBExpense, Transference as DBTransference

logger = utils.get_logger()

TZ = pytz.timezone("America/Santiago")


class Currency(Enum):
    USD = "usd"
    CLP = "clp"


class ExpenseCategory(Enum):
    GENERAL = "general"
    ONLINE_PLATFORM = "online_platform"  # kept from your original

    # New categories (English titles)
    FOOD = "food"
    EDUCATION = "education"
    TRANSPORT = "transport"
    SERVICES = "services"
    TRANSFERS = "transfers"
    CLOTHING = "clothing"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    LOAN = "loan"
    ATM_WITHDRAWAL = "atm_withdrawal"
    INVESTMENTS = "investments"
    HOUSING = "housing"
    EXTERNAL_FOOD = "external_food"
    RECREATION = "recreation"
    ONLINE = "online"
    COMMISSIONS = "commissions"
    TRAVEL = "travel"
    HEALTH = "health"
    FAMILY = "family"
    LAUNDRY = "laundry"
    BOOKS = "books"
    PURIFIED_WATER = "purified_water"

cat_json = ""

with open("categories.json", "r") as f:
    cat_json = f.read()
CATEGORY_KEYWORDS_RAW: dict[str, list[str]] = json.loads(cat_json)

# Map category display name -> Enum
CATEGORY_NAME_TO_ENUM: dict[str, ExpenseCategory] = {
    "Food": ExpenseCategory.FOOD,
    "Education": ExpenseCategory.EDUCATION,
    "Transport": ExpenseCategory.TRANSPORT,
    "Services": ExpenseCategory.SERVICES,
    "Transfers": ExpenseCategory.TRANSFERS,
    "Clothing": ExpenseCategory.CLOTHING,
    "Entertainment": ExpenseCategory.ENTERTAINMENT,
    "Sports": ExpenseCategory.SPORTS,
    "Loan": ExpenseCategory.LOAN,
    "ATM_withdrawal": ExpenseCategory.ATM_WITHDRAWAL,
    "Investments": ExpenseCategory.INVESTMENTS,
    "Housing": ExpenseCategory.HOUSING,
    "External_food": ExpenseCategory.EXTERNAL_FOOD,
    "Recreation": ExpenseCategory.RECREATION,
    "Online": ExpenseCategory.ONLINE,
    "Commissions": ExpenseCategory.COMMISSIONS,
    "Travel": ExpenseCategory.TRAVEL,
    "Health": ExpenseCategory.HEALTH,
    "Family": ExpenseCategory.FAMILY,
    "Laundry": ExpenseCategory.LAUNDRY,
    "Books": ExpenseCategory.BOOKS,
    "Purified_water": ExpenseCategory.PURIFIED_WATER,
}


def _normalize(s: str) -> str:
    """
    Normalize for robust substring matching:
    - NFKD + strip accents
    - Uppercase
    - Remove punctuation and extra spaces
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # Keep alnum and spaces only
    s = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in s)
    # Collapse spaces and uppercase
    s = " ".join(s.split()).upper()
    return s


# Precompute normalized keywords, also keep a flat list for longest-first matching
NORMALIZED_KEYWORDS: list[tuple[str, ExpenseCategory]] = []
for cat_name, keywords in CATEGORY_KEYWORDS_RAW.items():
    cat_enum = CATEGORY_NAME_TO_ENUM[cat_name]
    for kw in keywords:
        nkw = _normalize(kw)
        if nkw:
            NORMALIZED_KEYWORDS.append((nkw, cat_enum))

# Sort by keyword length DESC so more specific/longer phrases win ("THE NEW YORK TIMES" over "TIMES")
NORMALIZED_KEYWORDS.sort(key=lambda t: len(t[0]), reverse=True)


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
    def _match_category_by_text(text: str) -> ExpenseCategory:
        """
        Robust substring matching against any keyword in any category.
        Returns the first (longest keyword) match; falls back to GENERAL.
        """
        norm_text = _normalize(text)
        if not norm_text:
            return ExpenseCategory.GENERAL

        for nkw, cat in NORMALIZED_KEYWORDS:
            if nkw and nkw in norm_text:
                return cat

        return ExpenseCategory.GENERAL

    @staticmethod
    def _get_category(commerce_or_recipient_str: str) -> ExpenseCategory:
        return Transaction._match_category_by_text(commerce_or_recipient_str)


class Expense(Transaction):
    commerce: str

    # REGEX
    COMPRA_GIRO = r"compra|giro en Cajero"
    AMOUNT_REGEX = rf"(?:{COMPRA_GIRO}) por (\S+)"
    COMMERCE_REGEX = r"compra por \S+ con \D+\d+ en (\D+)?"
    DATE_REGEX = rf"(?:{COMPRA_GIRO}) por \S+ con \D+.* (?:en \D+)? .* el (\d+\d+/\d+/\d+\s+\d+:\d+)"

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
        # Clean and keep original casing for storage, but category matching uses normalized text
        return commerce_str.strip().strip("-").strip()

    # Date

    @classmethod
    def _get_date_str(cls, content: str) -> str:
        dates = re.findall(cls.DATE_REGEX, content)
        date = dates[0] if dates else ""
        return date

    def to_db_model(self) -> "DBExpense":
        """Convert to database model"""
        from models import Expense as DBExpense

        return DBExpense(
            commerce=self.commerce,
            amount=self.value,
            currency=self.currency,
            category=self.category,
            date=self.date,
            description="Extracted from email",
        )


class Transference(Transaction):
    recipient: str

    AMOUNT_REGEX = r"Monto\s*(\S+)"
    RECIPIENT_REGEX = r"(?:Nombre y Apellido |Nombre )(.*) Rut"

    def __init__(self, amount_str: str, recipient_str: str, date_str: str):
        self._parse_amount(amount_str)
        self.recipient = recipient_str.strip()
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

    def to_db_model(self) -> "DBTransference":
        """Convert to database model"""
        from models import Transference as DBTransference

        return DBTransference(
            recipient=self.recipient,
            amount=self.value,
            currency=self.currency,
            category=self.category,
            date=self.date,
            description="Extracted from email",
        )


def save_extracted_expense(content: str, session: Session) -> "DBExpense":
    """Extract expense from text content and save to database"""
    expense_parser = Expense.get_expense(content)
    db_expense = expense_parser.to_db_model()
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense


def save_extracted_transference(content: str, date_str: str, session: Session) -> "DBTransference":
    """Extract transference from text content and save to database"""
    transference_parser = Transference.get_transference(content, date_str)
    db_transference = transference_parser.to_db_model()
    session.add(db_transference)
    session.commit()
    session.refresh(db_transference)
    return db_transference
