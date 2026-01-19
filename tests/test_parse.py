import pytest
from datetime import datetime
from parsers.parser import EmailParser
from parsers.base import Currency, ExpenseCategory
from email_service.manager import Message
from parsers.transference import Transference
from parsers.expense import Expense

remitent = "test@test.com"
time_obj = datetime(year=2025, month=9, day=12, hour=12, minute=30)

BANK = "banco_chile"


def test_amount_data_usd():
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_usd.txt", encoding="utf-8") as f:
        usd_expense = f.read()
    with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg_usd = Message(remitent, subject, time_obj, usd_expense)
    expense = parser.get_expense(msg_usd)
    assert isinstance(expense, Expense)
    assert expense.value == 20.88
    assert expense.currency == Currency.USD
    assert expense.commerce == "APPLE.COM BILL CUPERTINO US"
    assert expense.category == ExpenseCategory.ONLINE, f"Invalid category for {expense.commerce}"
    assert expense.date == time_obj


@pytest.mark.parametrize(
    ("bank", "amount", "commerce", "cat"),
    [
        ("banco_chile", 38844, "STA ISABEL JM CAR", ExpenseCategory.FOOD),
        ("santander", 68885, "Entel pcs", ExpenseCategory.SERVICES),
    ],
)
def test_amount_data_clp(bank, amount, commerce, cat):
    parser = EmailParser(bank)
    parser.build_parser()
    with open(f"tests/banks/{bank}/purchase_clp.txt", encoding="utf-8") as f:
        clp_expense = f.read()
    with open(f"tests/banks/{bank}/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg_clp = Message(remitent, subject, time_obj, clp_expense)

    expense = parser.get_expense(msg_clp)
    assert isinstance(expense, Expense)
    assert expense.value == amount
    assert expense.commerce == commerce
    assert expense.currency == Currency.CLP
    assert expense.category == cat, f"Invalid category for {expense.commerce}"
    assert expense.date == time_obj


def test_amount_data_clp_with_number():
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_clp_number.txt", encoding="utf-8") as f:
        clp_expense_with_number = f.read()
    with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg_clp_num = Message(remitent, subject, time_obj, clp_expense_with_number)

    expense = parser.get_expense(msg_clp_num)
    assert isinstance(expense, Expense)
    assert expense.value == 22737.0
    assert expense.currency == Currency.CLP
    assert expense.commerce == "LOCAL 6496-12-12"
    assert expense.category == ExpenseCategory.GENERAL, f"Invalid category for {expense.commerce}"
    assert expense.date == time_obj


def test_parse_data_giro():
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/withdrawal.txt", encoding="utf-8") as f:
        data = f.read()
    with open("tests/banks/banco_chile/withdrawal_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message(remitent, subject, time_obj, data)
    expense = parser.get_expense(msg)
    assert isinstance(expense, Expense)
    assert expense.value == 20000.0
    assert expense.currency == Currency.CLP
    assert expense.category == ExpenseCategory.ATM_WITHDRAWAL
    assert expense.date == time_obj


@pytest.mark.parametrize(
    ("bank", "amount", "recipient"),
    [
        ("banco_chile", 6000, "Some Person"),
        ("santander", 53000, "JORGE IGNACIO CASTRO VELIZ"),
    ],
)
def test_parse_transference(bank, amount, recipient):
    parser = EmailParser(bank)
    parser.build_parser()
    with open(f"tests/banks/{bank}/transference.txt", encoding="utf-8") as f:
        data = f.read()
    with open(f"tests/banks/{bank}/transference_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message(remitent, subject, time_obj, data)

    transference = parser.get_transference(msg)
    assert isinstance(transference, Transference)
    assert transference.value == amount
    assert transference.currency == Currency.CLP
    assert transference.recipient == recipient
    assert transference.category == ExpenseCategory.GENERAL
    assert transference.date == time_obj


def test_parse_app_transference():
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/transference_app.txt", encoding="utf-8") as f:
        data = f.read()
    with open("tests/banks/banco_chile/transference_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message(remitent, subject, time_obj, data)

    transference = parser.get_transference(msg)
    assert isinstance(transference, Transference)
    assert transference.value == 10000.0
    assert transference.currency == Currency.CLP
    assert transference.recipient == "Medio De Pago Fintoc"
    assert transference.category == ExpenseCategory.FAMILY
    assert transference.date == time_obj
