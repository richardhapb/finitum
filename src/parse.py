import re
from datetime import datetime
from enum import Enum

import utils

logger = utils.get_logger()

AMOUNT_REGEX = r"compra por (\S+)"
COMPRA_GIRO = r"compra|giro en Cajero"
COMMERCE_REGEX = rf"(?:{COMPRA_GIRO}) por \S+ con \D+\d+ en (\D+)"
DATE_REGEX = rf"(?:{COMPRA_GIRO}) por \S+ con \D+\d+ en \D+.*(\d+\d+/\d+/\d+\s+\d+:\d+)"

class Currency(Enum):
    USD = "usd"
    CLP = "clp"

class ExpenseCategory(Enum):
    GENERAL = "general"
    ONLINE_PLATFORM = "online_platform"

class Expense:
    currency: Currency
    value: float
    category: ExpenseCategory
    commerce: str
    date: datetime

    def __init__(self, amount_str: str, commerce_str: str, date_str: str):
        self._parse_amount(amount_str)
        self.commerce = _sanitize_commerce_str(commerce_str)
        self.category = _get_category(self.commerce)
        try:
            self.date = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
        except ValueError:
            logger.exception("Error parsing date")
            self.date = datetime.now()


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

def get_expense(content: str) -> Expense:

    amount_str = _get_amount_str(content)
    commerce_str = _get_commerce_str(content)
    date_str = _get_date_str(content)

    return Expense(amount_str, commerce_str, date_str)

# Amount

def _get_amount_str(content: str) -> str:
    amounts = re.findall(AMOUNT_REGEX, content)
    amount = amounts[0] if amounts else ""
    return amount

# Commerce / Category

def _get_commerce_str(content: str) -> str:
    commerces = re.findall(COMMERCE_REGEX, content)
    commerce = commerces[0] if commerces else ""
    return commerce

def _get_category(commerce_str: str) -> ExpenseCategory:
    if commerce_str in ["Upwork"]:
        return ExpenseCategory.ONLINE_PLATFORM
    return ExpenseCategory.GENERAL

def _sanitize_commerce_str(commerce_str: str) -> str:
    return commerce_str.strip("").strip("-").strip()

# Date

def _get_date_str(content: str) -> str:
    dates = re.findall(DATE_REGEX, content)
    date = dates[0] if dates else ""
    return date

