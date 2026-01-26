import json
import re
from enum import Enum
from typing import Self

from requests.exceptions import JSONDecodeError
from sqlmodel import Session

from db.models import Expense as DbExpense
from db.models import Transference as DbTransference
from email_service.manager import Message
from utils.logger import get_logger
from parsers.expense import Expense
from parsers.transference import Transference
from parsers.transaction_mapper import transference_to_db_model, expense_to_db_model


logger = get_logger()


class ExpenseType(Enum):
    WITHDRAWAL = "withdrawal"
    PURCHASE = "purchase"
    TRANSFERENCE = "transference"


class BankNotFoundError(Exception):
    pass


class BankPatterns:
    # recipients
    remitents: list[str]

    # subject
    exclusions: list[str]
    withdrawal_pattern: str
    purchase_pattern: str
    transference_pattern: str

    # body
    commerce_regex: str
    amount_purchase_regex: str
    amount_withdrawal_regex: str
    amount_transference_regex: str
    date_regex: str
    transference_recipient_regex: str
    transference_matches_regex: str

    @classmethod
    def from_json(cls, filename: str, bank: str) -> Self:
        try:
            with open(filename, encoding="utf-8") as f:
                data = json.loads(f.read())
                bank_data = data[bank]
        except JSONDecodeError:
            logger.exception("Error decoding JSON")
            raise
        except IndexError as e:
            logger.error("Bank not found: %s", bank)
            raise BankNotFoundError from e
        except (OSError, ValueError) as e:
            logger.exception("Error loading file")
            raise BankNotFoundError from e

        for kw in "amountPurchase", "amountTransference", "amountWithdrawal", "date", "commerce":
            if kw not in bank_data.get("body", {}):
                raise BankNotFoundError("Keyword not found: %s", kw)
        for kw in "purchase", "withdrawal", "transference", "exclusions":
            if kw not in bank_data.get("subject", {}):
                raise BankNotFoundError("Keyword not found: %s", kw)

        obj = cls()
        try:
            obj.remitents = bank_data.get("remitents", [])
            subject = bank_data["subject"]
            obj.exclusions = subject["exclusions"]
            obj.withdrawal_pattern = subject["withdrawal"]
            obj.purchase_pattern = subject["purchase"]
            obj.transference_pattern = subject["transference"]

            body = bank_data["body"]
            obj.amount_purchase_regex = body["amountPurchase"]
            obj.amount_transference_regex = body["amountTransference"]
            obj.amount_withdrawal_regex = body["amountWithdrawal"]
            obj.commerce_regex = body["commerce"]
            obj.date_regex = body["date"]
            obj.transference_recipient_regex = body["transferenceRecipient"]
            obj.transference_matches_regex = body.get("transferenceMatches", "")
        except IndexError as e:
            logger.exception("pattern not found in bank json")
            raise BankNotFoundError from e
        else:
            return obj


class EmailParser:
    bank: str
    bank_patterns: BankPatterns

    def __init__(self, bank: str):
        self.bank = bank

    def build_parser(self) -> None:
        """
        Exctract the regexs from the json and extract the required patterns

        Can raise a `BankNotFoundError` if the json doesn't have all the required
        data to build the parser.
        """
        try:
            self.bank_patterns = self._get_regexs(self.bank)
        except JSONDecodeError as e:
            raise BankNotFoundError("Malformed JSON") from e
        except BankNotFoundError:
            logger.exception("Error retrieving required bank %s", self.bank)
            raise

    def _classify_message(self, message: Message) -> ExpenseType | None:
        subject = message.subject.lower()
        for exclusion in self.bank_patterns.exclusions:
            if exclusion in subject:
                return None

        if re.search(self.bank_patterns.purchase_pattern, subject, re.IGNORECASE):
            return ExpenseType.PURCHASE
        if re.search(self.bank_patterns.withdrawal_pattern, subject, re.IGNORECASE):
            return ExpenseType.WITHDRAWAL
        if re.search(self.bank_patterns.transference_pattern, subject, re.IGNORECASE):
            return ExpenseType.TRANSFERENCE

        return None

    @classmethod
    def _get_regexs(cls, bank: str) -> BankPatterns:
        return BankPatterns.from_json("src/parsers/regex.json", bank)

    def _get_commerce_str(self, msg: Message) -> str:
        commerces = re.findall(self.bank_patterns.commerce_regex, msg.body)
        commerce = commerces[0] if commerces else ""
        return commerce

    def _get_amount_str(self, msg: Message, expense_type: ExpenseType) -> str | None:
        match expense_type:
            case ExpenseType.PURCHASE:
                regex = self.bank_patterns.amount_purchase_regex
            case ExpenseType.WITHDRAWAL:
                regex = self.bank_patterns.amount_withdrawal_regex
            case ExpenseType.TRANSFERENCE:
                regex = self.bank_patterns.amount_transference_regex
            case _:
                return None

        amounts = re.findall(regex, msg.body)
        return amounts[0] if amounts else None

    def _get_transf_recipient_str(self, msg: Message) -> str:
        recipients = re.findall(self.bank_patterns.transference_recipient_regex, msg.body)
        recipient = recipients[0] if recipients else ""
        return recipient

    def _matches_transference_body(self, msg: Message) -> bool:
        """Check if the message body matches the transference pattern."""
        if not self.bank_patterns.transference_matches_regex:
            return True
        return bool(re.search(self.bank_patterns.transference_matches_regex, msg.body, re.IGNORECASE))

    @staticmethod
    def _extract_email_from_remitent(remitent: str) -> str:
        """Extract email address from formats like 'Name <email@domain.com>' or plain email."""
        match = re.search(r"<([^>]+)>", remitent)
        if match:
            return match.group(1).lower()
        return remitent.lower().strip()

    def _is_expected_remitent(self, msg: Message) -> bool:
        if not self.bank_patterns.remitents:
            return True

        extracted_email = self._extract_email_from_remitent(msg.remitent)
        return any(extracted_email == r.lower() for r in self.bank_patterns.remitents)

    def get_expense(self, msg: Message) -> Expense | None:
        if not self._is_expected_remitent(msg):
            logger.debug("Not expected remitent: %s", msg.remitent)
            return None

        expense_type = self._classify_message(msg)
        if not expense_type:
            return None
        amount_str = self._get_amount_str(msg, expense_type)

        if not amount_str:
            return None

        if expense_type == ExpenseType.WITHDRAWAL:
            commerce_str = "GIRO EN CAJERO"
        else:
            commerce_str = self._get_commerce_str(msg)
        return Expense(amount_str, commerce_str, msg.date)

    def get_transference(self, msg: Message) -> Transference | None:
        if not self._is_expected_remitent(msg):
            logger.debug("Not expected remitent: %s", msg.remitent)
            return None
        expense_type = self._classify_message(msg)
        if not expense_type:
            return None

        if not self._matches_transference_body(msg):
            logger.debug("Message body does not match transference pattern")
            return None

        amount_str = self._get_amount_str(msg, expense_type)
        if not amount_str:
            return None
        recipient_str = self._get_transf_recipient_str(msg)
        return Transference(amount_str, recipient_str, msg.date)


def save_expense(user_id: int, parser: EmailParser, msg: Message, session: Session) -> DbTransference | DbExpense | None:
    expense_type = parser._classify_message(msg)

    if expense_type == ExpenseType.TRANSFERENCE:
        logger.info("Saving transference")
        transference = parser.get_transference(msg)
        if not transference:
            return None
        db_transference = transference_to_db_model(transference)
        db_transference.user_id = user_id
        session.add(db_transference)
        session.commit()
        session.refresh(db_transference)
        return db_transference
    if expense_type in {ExpenseType.PURCHASE, ExpenseType.WITHDRAWAL}:
        logger.debug("Trying to save expense")
        expense = parser.get_expense(msg)
        if not expense:
            return None
        db_expense = expense_to_db_model(expense)
        db_expense.user_id = user_id
        session.add(db_expense)
        session.commit()
        session.refresh(db_expense)
        return db_expense

    return None
