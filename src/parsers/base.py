import json
import unicodedata
from datetime import datetime
from enum import Enum

from utils.logger import get_logger

logger = get_logger()


class Currency(Enum):
    USD = "usd"
    CLP = "clp"


class ExpenseCategory(Enum):
    GENERAL = "general"

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

with open("categories.json", encoding="utf-8") as f:
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
            logger.exception("Error parsing amount: %r", amount_str)
            self.value = 0.0

    # Amount

    @staticmethod
    def _match_category_by_text(text: str) -> ExpenseCategory:
        """
        Robust substring matching against any keyword in any category.
        Returns the first (longest keyword) match; falls back to GENERAL.
        """
        try:
            norm_text = _normalize(text)
            if not norm_text:
                return ExpenseCategory.GENERAL

            for nkw, cat in NORMALIZED_KEYWORDS:
                if nkw and nkw in norm_text:
                    return cat
        except Exception:
            logger.exception("Error matching category: %s")

        return ExpenseCategory.GENERAL

    @staticmethod
    def _get_category(commerce_or_recipient_str: str) -> ExpenseCategory:
        return Transaction._match_category_by_text(commerce_or_recipient_str)
