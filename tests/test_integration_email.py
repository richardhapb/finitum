from datetime import datetime
from unittest.mock import MagicMock

import pytest

from email_service.manager import Message
from parsers.parser import EmailParser, save_expense

remitent = "test@test.com"
banco_chile_remitent = "enviodigital@bancochile.cl"
time_obj = datetime(year=2025, month=9, day=12, hour=12, minute=30)

BANK = "banco_chile"


class TestSaveExpenseIntegration:
    """Integration tests for the save_expense function."""

    def test_save_expense_purchase(self):
        """Test saving an expense from a purchase email."""
        parser = EmailParser(BANK)
        parser.build_parser()
        with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
            expense_data = f.read()
        with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        msg = Message(banco_chile_remitent, subject, time_obj, expense_data)

        mock_session = MagicMock()
        result = save_expense(parser, msg, mock_session)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_save_expense_transference(self):
        """Test saving a transference from a transference email."""
        parser = EmailParser(BANK)
        parser.build_parser()
        with open("tests/banks/banco_chile/transference.txt", encoding="utf-8") as f:
            data = f.read()
        with open("tests/banks/banco_chile/transference_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        valid_remitent = "serviciodetransferencias@bancochile.cl"
        msg = Message(valid_remitent, subject, time_obj, data)

        mock_session = MagicMock()
        result = save_expense(parser, msg, mock_session)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_save_expense_withdrawal(self):
        """Test saving a withdrawal expense."""
        parser = EmailParser(BANK)
        parser.build_parser()
        with open("tests/banks/banco_chile/withdrawal.txt", encoding="utf-8") as f:
            data = f.read()
        with open("tests/banks/banco_chile/withdrawal_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        msg = Message(banco_chile_remitent, subject, time_obj, data)

        mock_session = MagicMock()
        result = save_expense(parser, msg, mock_session)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_save_expense_invalid_remitent_returns_none(self):
        """Test that invalid remitent returns None without saving."""
        parser = EmailParser(BANK)
        parser.build_parser()
        with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
            expense_data = f.read()
        with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        invalid_remitent = "spam@malicious.com"
        msg = Message(invalid_remitent, subject, time_obj, expense_data)

        mock_session = MagicMock()
        result = save_expense(parser, msg, mock_session)

        assert result is None
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_save_expense_unknown_subject_returns_none(self):
        """Test that unknown subject returns None without saving."""
        parser = EmailParser(BANK)
        parser.build_parser()

        msg = Message(banco_chile_remitent, "Unknown subject type", time_obj, "some body")

        mock_session = MagicMock()
        result = save_expense(parser, msg, mock_session)

        assert result is None
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_save_expense_exclusion_returns_none(self):
        """Test that excluded subject returns None without saving."""
        parser = EmailParser(BANK)
        parser.build_parser()

        msg = Message(banco_chile_remitent, "Transferencia entre mis cuentas", time_obj, "body")

        mock_session = MagicMock()
        result = save_expense(parser, msg, mock_session)

        assert result is None
        mock_session.add.assert_not_called()


@pytest.mark.parametrize(
    ("bank", "remitent_email", "expected_valid"),
    [
        ("banco_chile", "enviodigital@bancochile.cl", True),
        ("banco_chile", "serviciodetransferencias@bancochile.cl", True),
        ("banco_chile", "unknown@bancochile.cl", False),
        ("banco_chile", "spam@evil.com", False),
        ("banco_chile", "Banco de Chile <enviodigital@bancochile.cl>", True),
        ("banco_chile", "ENVIODIGITAL@BANCOCHILE.CL", True),
        ("santander", "mensajeria@santander.cl", True),
        ("santander", "invalid@santander.cl", False),
        ("santander", "Santander <mensajeria@santander.cl>", True),
    ],
)
def test_is_expected_remitent(bank, remitent_email, expected_valid):
    """Parametrized test for remitent validation across banks."""
    parser = EmailParser(bank)
    parser.build_parser()
    msg = Message(remitent_email, "Subject", time_obj, "Body")
    assert parser._is_expected_remitent(msg) == expected_valid
