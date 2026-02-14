"""Integration tests for the email task module."""

import pytest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from email_service.manager import Message, normalize_date_from
from parsers.parser import EmailParser
from parsers.base import Currency
from tasks.email_fetch import save_message, get_user_messages


# Test fixtures
banco_chile_remitent = "enviodigital@bancochile.cl"
transference_remitent = "serviciodetransferencias@bancochile.cl"
time_obj = datetime(year=2025, month=9, day=12, hour=12, minute=30)


class TestEmailTaskSaveMessage:
    """Integration tests for the save_message function in email task."""

    def test_save_message_with_valid_expense(self):
        """Test save_message correctly processes a valid expense email."""

        parser = EmailParser("banco_chile")
        parser.build_parser()

        with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
            body = f.read()
        with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        msg = Message(banco_chile_remitent, subject, time_obj, body)
        mock_session = MagicMock()

        result = save_message(1, parser, msg, mock_session)

        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_save_message_with_valid_transference(self):
        """Test save_message correctly processes a valid transference email."""

        parser = EmailParser("banco_chile")
        parser.build_parser()

        with open("tests/banks/banco_chile/transference.txt", encoding="utf-8") as f:
            body = f.read()
        with open("tests/banks/banco_chile/transference_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        msg = Message(transference_remitent, subject, time_obj, body)
        mock_session = MagicMock()

        result = save_message(1, parser, msg, mock_session)

        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_save_message_with_invalid_remitent(self):
        """Test save_message returns False for invalid remitent."""

        parser = EmailParser("banco_chile")
        parser.build_parser()

        with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
            body = f.read()
        with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        invalid_remitent = "spam@malicious.com"
        msg = Message(invalid_remitent, subject, time_obj, body)
        mock_session = MagicMock()

        result = save_message(1, parser, msg, mock_session)

        assert result is False
        mock_session.add.assert_not_called()

    def test_save_message_with_unknown_subject(self):
        """Test save_message returns False for unknown email type."""

        parser = EmailParser("banco_chile")
        parser.build_parser()

        msg = Message(banco_chile_remitent, "Random unknown subject", time_obj, "Some body")
        mock_session = MagicMock()

        result = save_message(1, parser, msg, mock_session)

        assert result is False
        mock_session.add.assert_not_called()

    def test_save_message_with_excluded_subject(self):
        """Test save_message returns False for excluded subject patterns."""

        parser = EmailParser("banco_chile")
        parser.build_parser()

        msg = Message(transference_remitent, "Transferencia entre mis cuentas", time_obj, "body")
        mock_session = MagicMock()

        result = save_message(1, parser, msg, mock_session)

        assert result is False
        mock_session.add.assert_not_called()


class TestEmailTaskEndToEnd:
    """End-to-end integration tests for the email task flow."""

    @patch("tasks.email_fetch.get_session")
    @patch("tasks.email_fetch.EmailManager")
    @patch("tasks.email_fetch.md.rebuild_credentials")
    def test_get_user_messages_processes_multiple_messages(
        self, mock_rebuild_credentials, mock_email_manager_class, mock_get_session
    ):
        """Test that get_user_messages processes multiple messages correctly."""

        # Setup mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.bank = "banco_chile"
        mock_user.last_update = datetime(2025, 1, 1)

        # Setup mock credentials object
        mock_creds_obj = MagicMock()

        # Setup mock session with exec returning user and credentials
        mock_session = MagicMock()
        mock_exec_user = MagicMock()
        mock_exec_user.one.return_value = mock_user
        mock_exec_creds = MagicMock()
        mock_exec_creds.one.return_value = mock_creds_obj
        mock_session.exec.side_effect = [mock_exec_user, mock_exec_creds]

        # Make get_session return a generator that yields a context manager
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=mock_session)
        mock_context_manager.__exit__ = MagicMock(return_value=False)
        mock_get_session.return_value = iter([mock_context_manager])

        # Setup mock rebuild_credentials
        mock_rebuild_credentials.return_value = MagicMock()

        # Setup mock EmailManager with messages
        with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
            body = f.read()
        with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        mock_messages = [
            Message(banco_chile_remitent, subject, time_obj, body),
            Message(banco_chile_remitent, subject, time_obj, body),
        ]
        mock_em_instance = MagicMock()
        mock_em_instance.get_messages.return_value = mock_messages
        mock_email_manager_class.return_value = mock_em_instance

        # Execute the task (calling the underlying function, not the Celery task)
        get_user_messages(user_id=1)

        # Verify EmailManager was called with rebuilt credentials
        mock_rebuild_credentials.assert_called_once_with(mock_creds_obj)
        mock_email_manager_class.assert_called_once()

        # Verify messages were fetched
        mock_em_instance.get_messages.assert_called_once()

        # Verify session.add was called for each valid message (2 times) +  update `last_update`
        assert mock_session.add.call_count == 3
        assert mock_session.commit.call_count == 3

    @patch("tasks.email_fetch.get_session")
    @patch("tasks.email_fetch.EmailManager")
    @patch("tasks.email_fetch.md.rebuild_credentials")
    def test_get_user_messages_uses_user_bank(
        self, mock_rebuild_credentials, mock_email_manager_class, mock_get_session
    ):
        """Test that get_user_messages uses user.bank for parser initialization."""

        # Setup mock user with santander bank
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.bank = "santander"
        mock_user.last_update = datetime(2025, 1, 1)

        mock_creds_obj = MagicMock()

        mock_session = MagicMock()
        mock_exec_user = MagicMock()
        mock_exec_user.one.return_value = mock_user
        mock_exec_creds = MagicMock()
        mock_exec_creds.one.return_value = mock_creds_obj
        mock_session.exec.side_effect = [mock_exec_user, mock_exec_creds]

        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=mock_session)
        mock_context_manager.__exit__ = MagicMock(return_value=False)
        mock_get_session.return_value = iter([mock_context_manager])

        mock_rebuild_credentials.return_value = MagicMock()

        # Setup mock EmailManager with santander messages
        with open("tests/banks/santander/purchase_clp.txt", encoding="utf-8") as f:
            body = f.read()
        with open("tests/banks/santander/purchase_subject.txt", encoding="utf-8") as f:
            subject = f.read().strip()

        mock_messages = [Message("mensajeria@santander.cl", subject, time_obj, body)]
        mock_em_instance = MagicMock()
        mock_em_instance.get_messages.return_value = mock_messages
        mock_email_manager_class.return_value = mock_em_instance

        # Execute
        get_user_messages(user_id=1)

        # Verify message was processed with correct santander remitent
        # + last_update save
        assert mock_session.add.call_count == 2

    @patch("tasks.email_fetch.get_session")
    @patch("tasks.email_fetch.md.rebuild_credentials")
    def test_get_user_messages_handles_missing_credentials(self, mock_rebuild_credentials, mock_get_session):
        """Test that get_user_messages handles missing credentials gracefully."""

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.bank = "banco_chile"
        mock_user.last_update = datetime(2025, 1, 1)

        mock_session = MagicMock()
        mock_exec_user = MagicMock()
        mock_exec_user.one.return_value = mock_user
        mock_exec_creds = MagicMock()
        mock_exec_creds.one.return_value = None  # No credentials
        mock_session.exec.side_effect = [mock_exec_user, mock_exec_creds]

        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=mock_session)
        mock_context_manager.__exit__ = MagicMock(return_value=False)
        mock_get_session.return_value = iter([mock_context_manager])

        # Should not call rebuild_credentials if credentials_obj is None
        get_user_messages(user_id=1)

        mock_rebuild_credentials.assert_not_called()

    @patch("tasks.email_fetch.get_session")
    @patch("tasks.email_fetch.EmailManager")
    @patch("tasks.email_fetch.md.rebuild_credentials")
    def test_get_user_messages_uses_unix_after_query(
        self, mock_rebuild_credentials, mock_email_manager_class, mock_get_session
    ):
        original_last_update = datetime(2026, 2, 14, 2, 0, 0)  # naive UTC from DB
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.bank = "banco_chile"
        mock_user.last_update = original_last_update

        mock_creds_obj = MagicMock()
        mock_creds_obj.is_valid = True

        mock_session = MagicMock()
        mock_exec_user = MagicMock()
        mock_exec_user.one.return_value = mock_user
        mock_exec_creds = MagicMock()
        mock_exec_creds.one.return_value = mock_creds_obj
        mock_session.exec.side_effect = [mock_exec_user, mock_exec_creds]

        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=mock_session)
        mock_context_manager.__exit__ = MagicMock(return_value=False)
        mock_get_session.return_value = iter([mock_context_manager])

        mock_rebuild_credentials.return_value = MagicMock()

        mock_em_instance = MagicMock()
        mock_em_instance.get_messages.return_value = []
        mock_email_manager_class.return_value = mock_em_instance

        get_user_messages(user_id=1)

        expected_last = normalize_date_from(original_last_update)
        expected_query = f"after:{int(expected_last.astimezone(UTC).timestamp())}"

        mock_em_instance.get_messages.assert_called_once_with(expected_query, date_from=expected_last)


class TestBankPatternIntegration:
    """Integration tests for bank pattern matching across different banks."""

    @pytest.mark.parametrize(
        ("bank", "fixture_file", "subject_file", "expected_type", "remitent"),
        [
            ("banco_chile", "purchase_clp.txt", "purchase_subject.txt", "expense", banco_chile_remitent),
            ("banco_chile", "withdrawal.txt", "withdrawal_subject.txt", "expense", banco_chile_remitent),
            ("banco_chile", "transference.txt", "transference_subject.txt", "transference", transference_remitent),
            ("santander", "purchase_clp.txt", "purchase_subject.txt", "expense", "mensajeria@santander.cl"),
            ("santander", "transference.txt", "transference_subject.txt", "transference", "mensajeria@santander.cl"),
        ],
    )
    def test_bank_patterns_integration(self, bank, fixture_file, subject_file, expected_type, remitent):
        """Test that all bank patterns correctly identify their transaction types."""
        parser = EmailParser(bank)
        parser.build_parser()

        with open(f"tests/banks/{bank}/{fixture_file}", encoding="utf-8") as f:
            body = f.read()
        with open(f"tests/banks/{bank}/{subject_file}", encoding="utf-8") as f:
            subject = f.read()

        msg = Message(remitent, subject, time_obj, body)

        if expected_type == "expense":
            result = parser.get_expense(msg)
            assert result is not None, f"Expected expense for {bank}/{fixture_file}"
            assert result.value > 0
            assert result.currency in {Currency.CLP, Currency.USD}
        elif expected_type == "transference":
            result = parser.get_transference(msg)
            assert result is not None, f"Expected transference for {bank}/{fixture_file}"
            assert result.value > 0
            assert result.recipient

    def test_all_banco_chile_remitents_work(self):
        """Test that both valid banco_chile remitents are accepted."""
        parser = EmailParser("banco_chile")
        parser.build_parser()

        with open("tests/banks/banco_chile/purchase_clp.txt", encoding="utf-8") as f:
            body = f.read()
        with open("tests/banks/banco_chile/purchase_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        valid_remitents = [
            "enviodigital@bancochile.cl",
            "serviciodetransferencias@bancochile.cl",
        ]

        for valid_remitent in valid_remitents:
            msg = Message(valid_remitent, subject, time_obj, body)
            expense = parser.get_expense(msg)
            assert expense is not None, f"Expected valid expense for remitent: {valid_remitent}"


class TestTransferenceMatchesIntegration:
    """Integration tests for transference body matching."""

    def test_transference_with_valid_body_saves(self):
        """Test that transference with valid body pattern saves correctly."""

        parser = EmailParser("banco_chile")
        parser.build_parser()

        with open("tests/banks/banco_chile/transference.txt", encoding="utf-8") as f:
            body = f.read()
        with open("tests/banks/banco_chile/transference_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        msg = Message(transference_remitent, subject, time_obj, body)
        mock_session = MagicMock()

        result = save_message(1, parser, msg, mock_session)

        assert result is True
        mock_session.add.assert_called_once()

    def test_transference_with_invalid_body_not_saved(self):
        """Test that transference with invalid body pattern is not saved."""

        parser = EmailParser("banco_chile")
        parser.build_parser()

        invalid_body = "Este correo no contiene el patron de transferencia esperado"
        msg = Message(transference_remitent, "Transferencia", time_obj, invalid_body)
        mock_session = MagicMock()

        result = save_message(1, parser, msg, mock_session)

        assert result is False
        mock_session.add.assert_not_called()

    def test_santander_transference_any_body_saves(self):
        """Test that santander transference with any body saves (empty transference_matches pattern)."""

        parser = EmailParser("santander")
        parser.build_parser()

        with open("tests/banks/santander/transference.txt", encoding="utf-8") as f:
            body = f.read()
        with open("tests/banks/santander/transference_subject.txt", encoding="utf-8") as f:
            subject = f.read()

        msg = Message("mensajeria@santander.cl", subject, time_obj, body)
        mock_session = MagicMock()

        result = save_message(1, parser, msg, mock_session)

        assert result is True
        mock_session.add.assert_called_once()


class TestUserBankIntegration:
    """Tests for user.bank field integration."""

    def test_user_model_has_bank_field(self):
        """Test that User model has bank field with default."""
        from db.models import User

        user = User(username="test", email="test@test.com")
        assert hasattr(user, "bank")
        assert user.bank == "banco_chile"

    def test_parser_uses_user_bank(self):
        """Test that parser can be initialized with different banks."""
        for bank in ["banco_chile", "santander"]:
            parser = EmailParser(bank)
            parser.build_parser()
            assert parser.bank == bank
