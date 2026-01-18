from datetime import datetime
from parsers.base import Transaction

from utils.logger import get_logger


logger = get_logger()


class Expense(Transaction):
    commerce: str

    def __init__(self, amount_str: str, commerce_str: str, date: datetime):
        self._parse_amount(amount_str)
        self.commerce = self._sanitize_commerce_str(commerce_str)
        self.category = self._get_category(self.commerce)
        self.date = date

    # Commerce / Category

    @staticmethod
    def _sanitize_commerce_str(commerce_str: str) -> str:
        # Clean and keep original casing for storage, but category matching uses normalized text
        return commerce_str.strip().strip("-").strip()
