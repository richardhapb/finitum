from datetime import datetime

from parsers.base import Transaction
from utils.logger import get_logger

logger = get_logger()


class Transference(Transaction):
    recipient: str

    def __init__(self, amount_str: str, recipient_str: str, date: datetime):
        self._parse_amount(amount_str)
        self.recipient = recipient_str.strip()
        self.category = self._get_category(self.recipient)
        self.date = date
