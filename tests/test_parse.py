from datetime import datetime

import pytest

from email_service.manager import Message
from parsers.base import Currency, ExpenseCategory
from parsers.expense import Expense
from parsers.parser import EmailParser, ExpenseType
from parsers.transference import Transference

remitent = "test@test.com"
banco_chile_remitent = "enviodigital@bancochile.cl"
santander_remitent = "mensajeria@santander.cl"
time_obj = datetime(year=2025, month=9, day=12, hour=12, minute=30)

BANK = "banco_chile"


def test_amount_data_usd():
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_usd.txt", encoding="utf-8") as f:
        usd_expense = f.read()
    with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg_usd = Message(banco_chile_remitent, subject, time_obj, usd_expense)
    expense = parser.get_expense(msg_usd)
    assert isinstance(expense, Expense)
    assert expense.value == 20.88
    assert expense.currency == Currency.USD
    assert expense.commerce == "APPLE.COM BILL CUPERTINO US"
    assert expense.category == ExpenseCategory.ONLINE, f"Invalid category for {expense.commerce}"
    assert expense.date == time_obj


@pytest.mark.parametrize(
    ("bank", "amount", "commerce", "cat", "test_remitent"),
    [
        ("banco_chile", 38844, "STA ISABEL JM CAR", ExpenseCategory.FOOD, banco_chile_remitent),
        ("santander", 68885, "Entel pcs", ExpenseCategory.SERVICES, santander_remitent),
    ],
)
def test_amount_data_clp(bank, amount, commerce, cat, test_remitent):
    parser = EmailParser(bank)
    parser.build_parser()
    with open(f"tests/banks/{bank}/purchase_clp.txt", encoding="utf-8") as f:
        clp_expense = f.read()
    with open(f"tests/banks/{bank}/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg_clp = Message(test_remitent, subject, time_obj, clp_expense)

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

    msg_clp_num = Message(banco_chile_remitent, subject, time_obj, clp_expense_with_number)

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

    msg = Message(banco_chile_remitent, subject, time_obj, data)
    expense = parser.get_expense(msg)
    assert isinstance(expense, Expense)
    assert expense.value == 20000.0
    assert expense.currency == Currency.CLP
    assert expense.category == ExpenseCategory.ATM_WITHDRAWAL
    assert expense.date == time_obj


@pytest.mark.parametrize(
    ("bank", "amount", "recipient", "test_remitent"),
    [
        ("banco_chile", 6000, "Some Person", "serviciodetransferencias@bancochile.cl"),
        ("santander", 53000, "Pablo Farfan", santander_remitent),
    ],
)
def test_parse_transference(bank, amount, recipient, test_remitent):
    parser = EmailParser(bank)
    parser.build_parser()
    with open(f"tests/banks/{bank}/transference.txt", encoding="utf-8") as f:
        data = f.read()
    with open(f"tests/banks/{bank}/transference_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message(test_remitent, subject, time_obj, data)

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

    msg = Message("serviciodetransferencias@bancochile.cl", subject, time_obj, data)

    transference = parser.get_transference(msg)
    assert isinstance(transference, Transference)
    assert transference.value == 10000.0
    assert transference.currency == Currency.CLP
    assert transference.recipient == "Medio De Pago Fintoc"
    assert transference.category == ExpenseCategory.FAMILY
    assert transference.date == time_obj


# REMITENT VALIDATION TESTS


def test_remitent_validation_valid_banco_chile():
    """Test that valid banco_chile remitent is accepted."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
        clp_expense = f.read()
    with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message(banco_chile_remitent, subject, time_obj, clp_expense)
    expense = parser.get_expense(msg)
    assert expense is not None
    assert isinstance(expense, Expense)


def test_remitent_validation_invalid_banco_chile():
    """Test that invalid remitent for banco_chile is rejected."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
        clp_expense = f.read()
    with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    invalid_remitent = "spam@malicious.com"
    msg = Message(invalid_remitent, subject, time_obj, clp_expense)
    expense = parser.get_expense(msg)
    assert expense is None


def test_remitent_validation_transference_valid():
    """Test that valid remitent for transferences is accepted."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/transference.txt", encoding="utf-8") as f:
        data = f.read()
    with open("tests/banks/banco_chile/transference_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    valid_remitent = "serviciodetransferencias@bancochile.cl"
    msg = Message(valid_remitent, subject, time_obj, data)
    transference = parser.get_transference(msg)
    assert transference is not None
    assert isinstance(transference, Transference)


def test_remitent_validation_transference_invalid():
    """Test that invalid remitent for transferences is rejected."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/transference.txt", encoding="utf-8") as f:
        data = f.read()
    with open("tests/banks/banco_chile/transference_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    invalid_remitent = "fake@phishing.com"
    msg = Message(invalid_remitent, subject, time_obj, data)
    transference = parser.get_transference(msg)
    assert transference is None


def test_remitent_validation_santander():
    """Test that valid santander remitent is accepted."""
    parser = EmailParser("santander")
    parser.build_parser()
    with open("tests/banks/santander/purchase_clp.txt", encoding="utf-8") as f:
        expense_data = f.read()
    with open("tests/banks/santander/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message(santander_remitent, subject, time_obj, expense_data)
    expense = parser.get_expense(msg)
    assert expense is not None
    assert isinstance(expense, Expense)


def test_remitent_extraction_with_name():
    """Test that remitent with format 'Name <email>' is correctly extracted."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
        clp_expense = f.read()
    with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    # Test with "Name <email>" format
    remitent_with_name = "Banco de Chile <enviodigital@bancochile.cl>"
    msg = Message(remitent_with_name, subject, time_obj, clp_expense)
    expense = parser.get_expense(msg)
    assert expense is not None
    assert isinstance(expense, Expense)


def test_remitent_extraction_plain_email():
    """Test that plain email remitent works."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
        clp_expense = f.read()
    with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message(banco_chile_remitent, subject, time_obj, clp_expense)
    expense = parser.get_expense(msg)
    assert expense is not None


def test_remitent_extraction_case_insensitive():
    """Test that remitent matching is case insensitive."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
        clp_expense = f.read()
    with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    # Test with uppercase email
    remitent_upper = "ENVIODIGITAL@BANCOCHILE.CL"
    msg = Message(remitent_upper, subject, time_obj, clp_expense)
    expense = parser.get_expense(msg)
    assert expense is not None


# REGEX PATTERN TESTS


def test_purchase_pattern_compra_con_tarjeta():
    """Test that the new 'compra con tarjeta' pattern is matched."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/purchase_card.txt", encoding="utf-8") as f:
        expense_data = f.read()
    with open("tests/banks/banco_chile/purchase_card_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message(banco_chile_remitent, subject, time_obj, expense_data)
    expense = parser.get_expense(msg)
    assert expense is not None
    assert isinstance(expense, Expense)
    assert expense.value == 15990.0
    assert expense.currency == Currency.CLP
    assert expense.commerce == "MERCADO PAGO"


def test_classify_message_purchase_cargo_en_cuenta():
    """Test that 'cargo en cuenta' subject is classified as PURCHASE."""
    parser = EmailParser(BANK)
    parser.build_parser()

    msg = Message(banco_chile_remitent, "Cargo en cuenta", time_obj, "body")
    expense_type = parser._classify_message(msg)
    assert expense_type == ExpenseType.PURCHASE


def test_classify_message_purchase_compra_con_tarjeta():
    """Test that 'compra con tarjeta' subject is classified as PURCHASE."""
    parser = EmailParser(BANK)
    parser.build_parser()

    msg = Message(banco_chile_remitent, "Compra con Tarjeta de Crédito", time_obj, "body")
    expense_type = parser._classify_message(msg)
    assert expense_type == ExpenseType.PURCHASE


def test_classify_message_exclusion():
    """Test that exclusion pattern rejects the message."""
    parser = EmailParser(BANK)
    parser.build_parser()

    msg = Message(banco_chile_remitent, "Transferencia entre mis cuentas", time_obj, "body")
    expense_type = parser._classify_message(msg)
    assert expense_type is None


def test_classify_message_withdrawal():
    """Test that 'giro' subject is classified as WITHDRAWAL."""
    parser = EmailParser(BANK)
    parser.build_parser()

    msg = Message(banco_chile_remitent, "Giro en cajero", time_obj, "body")
    expense_type = parser._classify_message(msg)
    assert expense_type == ExpenseType.WITHDRAWAL


def test_classify_message_transference():
    """Test that 'transferencia' subject is classified as TRANSFERENCE."""
    parser = EmailParser(BANK)
    parser.build_parser()

    msg = Message(banco_chile_remitent, "Transferencia realizada", time_obj, "body")
    expense_type = parser._classify_message(msg)
    assert expense_type == ExpenseType.TRANSFERENCE


# TRANSFERENCE MATCHES TESTS


def test_transference_matches_has_realizado():
    """Test that 'has realizado' in body matches transference pattern."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/transference.txt", encoding="utf-8") as f:
        data = f.read()
    with open("tests/banks/banco_chile/transference_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message("serviciodetransferencias@bancochile.cl", subject, time_obj, data)
    assert parser._matches_transference_body(msg) is True


def test_transference_matches_ha_efectuado():
    """Test that 'ha efectuado' in body matches transference pattern."""
    parser = EmailParser(BANK)
    parser.build_parser()
    with open("tests/banks/banco_chile/transference_app.txt", encoding="utf-8") as f:
        data = f.read()
    with open("tests/banks/banco_chile/transference_subject.txt", encoding="utf-8") as f:
        subject = f.read()

    msg = Message("serviciodetransferencias@bancochile.cl", subject, time_obj, data)
    assert parser._matches_transference_body(msg) is True


def test_transference_matches_invalid_body():
    """Test that body without transference pattern is rejected."""
    parser = EmailParser(BANK)
    parser.build_parser()

    invalid_body = "Este es un correo sin el patron de transferencia"
    msg = Message("serviciodetransferencias@bancochile.cl", "Transferencia", time_obj, invalid_body)
    assert parser._matches_transference_body(msg) is False


def test_transference_matches_empty_pattern():
    """Test that empty transference pattern (santander) accepts any body."""
    parser = EmailParser("santander")
    parser.build_parser()

    any_body = "Any body content without the pattern"
    msg = Message(santander_remitent, "Transferencia de fondos", time_obj, any_body)
    assert parser._matches_transference_body(msg) is True


def test_get_transference_with_invalid_body_returns_none():
    """Test that get_transference returns None if body doesn't match pattern."""
    parser = EmailParser(BANK)
    parser.build_parser()

    invalid_body = "Este es un correo sin el patron de transferencia"
    msg = Message("serviciodetransferencias@bancochile.cl", "Transferencia", time_obj, invalid_body)
    transference = parser.get_transference(msg)
    assert transference is None


def test_bank_patterns_transference_matches_loaded():
    """Test that transference_matches_regex is loaded from JSON."""
    parser = EmailParser(BANK)
    parser.build_parser()
    assert parser.bank_patterns.transference_matches_regex == "(?:has realizado|ha efectuado)"


def test_bank_patterns_transference_matches_empty():
    """Test that empty transference_matches_regex is handled."""
    parser = EmailParser("santander")
    parser.build_parser()
    assert not parser.bank_patterns.transference_matches_regex


@pytest.mark.parametrize(
    ("bank", "expected_pattern"),
    [
        ("banco_chile", "(?:has realizado|ha efectuado)"),
        ("santander", ""),
    ],
)
def test_transference_matches_regex_by_bank(bank, expected_pattern):
    """Parametrized test for transference_matches_regex across banks."""
    parser = EmailParser(bank)
    parser.build_parser()
    assert parser.bank_patterns.transference_matches_regex == expected_pattern
