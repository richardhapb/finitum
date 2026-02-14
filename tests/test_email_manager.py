from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from email_service.manager import Message, normalize_date_from


@pytest.fixture
def message_factory() -> Callable[[datetime], Message]:
    def _create(date: datetime) -> Message:
        return Message(
            remitent="test",
            subject="this is a test",
            date=date,
            body="Hello from the test",
        )

    return _create


def test_is_after_date_from_respect_hour(message_factory):
    msg_date = datetime(year=2026, month=1, day=4, hour=11, minute=0)
    date_from = datetime(year=2026, month=1, day=4, hour=15, minute=0)

    msg = message_factory(msg_date)

    assert not msg._is_after_date_from(msg_date, date_from)


def test_is_after_date_from_respect_date(message_factory):
    msg_date = datetime(year=2026, month=1, day=4, hour=11, minute=0)
    date_from = datetime(year=2026, month=1, day=5, hour=11, minute=0)

    msg = message_factory(msg_date)

    assert not msg._is_after_date_from(msg_date, date_from)


def test_is_after_date_from_accept_hour(message_factory):
    msg_date = datetime(year=2026, month=1, day=4, hour=11, minute=0)
    date_from = datetime(year=2026, month=1, day=4, hour=9, minute=0)

    msg = message_factory(msg_date)

    assert msg._is_after_date_from(msg_date, date_from)


def test_is_after_date_from_accept_date(message_factory):
    msg_date = datetime(year=2026, month=1, day=4, hour=11, minute=0)
    date_from = datetime(year=2026, month=1, day=3, hour=10, minute=0)

    msg = message_factory(msg_date)

    assert msg._is_after_date_from(msg_date, date_from)


def test_is_after_date_from_reject_exact_time(message_factory):
    msg_date = datetime(year=2026, month=1, day=4, hour=11, minute=0)
    date_from = datetime(year=2026, month=1, day=4, hour=11, minute=0)

    msg = message_factory(msg_date)

    assert not msg._is_after_date_from(msg_date, date_from)


def test_normalize_date_from_naive_is_treated_as_utc():
    naive = datetime(2026, 2, 14, 2, 0, 0)

    normalized = normalize_date_from(naive)

    assert normalized is not None
    assert normalized.tzinfo is not None
    assert normalized.timestamp() == pytest.approx(naive.replace(tzinfo=UTC).timestamp())
