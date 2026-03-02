from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from db.models import Expense as DbExpense
from db.models import Transference as DbTransference
from db.models import User
from email_service.manager import Message
from parsers.parser import EmailParser, save_expense

remitent = "test@test.com"
banco_chile_remitent = "enviodigital@bancochile.cl"
time_obj = datetime(year=2025, month=9, day=12, hour=12, minute=30)

BANK = "banco_chile"


def create_user(session: Session, username: str, email: str) -> User:
    user = User.create(username=username, email=email, password="password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


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

        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            user = create_user(session, "purchase-user", "purchase@example.com")
            result = save_expense(user.id, parser, msg, session)
            saved_expenses = session.exec(select(DbExpense)).all()

            assert result is not None
            assert len(saved_expenses) == 1
            assert saved_expenses[0].id == result.id
            assert saved_expenses[0].user_id == user.id
            assert saved_expenses[0].commerce == "STA ISABEL JM CAR"
            assert saved_expenses[0].category_id is not None

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

        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            user = create_user(session, "transference-user", "transference@example.com")
            result = save_expense(user.id, parser, msg, session)
            saved_transferences = session.exec(select(DbTransference)).all()

            assert result is not None
            assert len(saved_transferences) == 1
            assert saved_transferences[0].id == result.id
            assert saved_transferences[0].user_id == user.id

    def test_save_expense_withdrawal(self):
        """Test saving a withdrawal expense."""
        parser = EmailParser(BANK)
        parser.build_parser()
        with open("tests/banks/banco_chile/withdrawal.txt", encoding="utf-8") as f:
            data = f.read()
        with open("tests/banks/banco_chile/withdrawal_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        msg = Message(banco_chile_remitent, subject, time_obj, data)

        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            user = create_user(session, "withdrawal-user", "withdrawal@example.com")
            result = save_expense(user.id, parser, msg, session)
            saved_expenses = session.exec(select(DbExpense)).all()

            assert result is not None
            assert len(saved_expenses) == 1
            assert saved_expenses[0].id == result.id
            assert saved_expenses[0].user_id == user.id
            assert saved_expenses[0].commerce == "GIRO EN CAJERO"
            assert saved_expenses[0].category_id is not None

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
        result = save_expense(1, parser, msg, mock_session)

        assert result is None
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_save_expense_unknown_subject_returns_none(self):
        """Test that unknown subject returns None without saving."""
        parser = EmailParser(BANK)
        parser.build_parser()

        msg = Message(banco_chile_remitent, "Unknown subject type", time_obj, "some body")

        mock_session = MagicMock()
        result = save_expense(1, parser, msg, mock_session)

        assert result is None
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_save_expense_exclusion_returns_none(self):
        """Test that excluded subject returns None without saving."""
        parser = EmailParser(BANK)
        parser.build_parser()

        msg = Message(banco_chile_remitent, "Transferencia entre mis cuentas", time_obj, "body")

        mock_session = MagicMock()
        result = save_expense(1, parser, msg, mock_session)

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
