"""End-to-end tests for the forwarding ingestion webhook (Phase 2).

Posts raw MIME fixtures to ``/ingest/email`` with a valid HMAC signature and
asserts the expense/transference is persisted through the existing pipeline.
"""

import hashlib
import hmac
from collections.abc import Iterator
from email.message import EmailMessage as PyEmailMessage
from email.utils import format_datetime
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from api import server
from db.models import Expense as DbExpense
from db.models import Transference as DbTransference
from db.models import User
from db.service import get_session

INGEST_SECRET = "test-ingest-secret"
BANCO_CHILE_PURCHASE_SENDER = "enviodigital@bancochile.cl"
BANCO_CHILE_TRANSFER_SENDER = "serviciodetransferencias@bancochile.cl"


class FakeRedis:
    """Minimal in-memory Redis stand-in for the bits the webhook touches."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def ping(self):
        return True

    def get(self, key):
        value = self.store.get(key)
        return value.encode() if isinstance(value, str) else value

    def set(self, key, value, *, nx=False, ex=None):  # noqa: ARG002
        if nx and key in self.store:
            return None
        self.store[key] = value
        return True

    def setex(self, key, _ttl, value):
        self.store[key] = value
        return True


def build_raw_email(sender: str, subject: str, body: str, *, message_id: str = "<m1@bank>") -> bytes:
    msg = PyEmailMessage()
    msg["From"] = sender
    msg["To"] = "user@example.com"
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(UTC))
    msg["Message-ID"] = message_id
    msg.set_content(body)
    return msg.as_bytes()


def sign(body: bytes) -> str:
    return "sha256=" + hmac.new(INGEST_SECRET.encode(), body, hashlib.sha256).hexdigest()


def read_fixture(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def engine():
    # Shared in-memory DB usable across TestClient's worker thread.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(engine, monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(server, "redis_client", fake_redis)
    monkeypatch.setattr(server, "INGEST_WEBHOOK_SECRET", INGEST_SECRET)
    # ingest.* reads the secret via the argument passed by the endpoint, so
    # patching the server-level constant is sufficient.

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    server.app.dependency_overrides[get_session] = override_session
    test_client = TestClient(server.app)
    test_client.fake_redis = fake_redis
    yield test_client
    server.app.dependency_overrides.clear()


def make_user(engine, token: str = "abc123token", bank: str = "banco_chile") -> User:  # noqa: S107
    with Session(engine) as session:
        user = User(username="forward-user", email="forward@example.com", bank=bank, ingest_token=token)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def post_email(client, raw: bytes, token: str):
    return client.post(
        f"/ingest/email?recipient=u-{token}@in.finitum.app",
        content=raw,
        headers={"X-Finitum-Signature": sign(raw), "Content-Type": "message/rfc822"},
    )


def test_ingest_purchase_persists_expense(client, engine):
    user = make_user(engine)
    raw = build_raw_email(
        BANCO_CHILE_PURCHASE_SENDER,
        read_fixture("tests/banks/banco_chile/purchase_subject.txt"),
        read_fixture("tests/banks/banco_chile/purchase_clp.txt"),
    )

    response = post_email(client, raw, user.ingest_token)

    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    with Session(engine) as session:
        expenses = session.exec(select(DbExpense)).all()
        assert len(expenses) == 1
        assert expenses[0].user_id == user.id
        assert expenses[0].commerce == "STA ISABEL JM CAR"


def test_ingest_transference_persists(client, engine):
    user = make_user(engine)
    raw = build_raw_email(
        BANCO_CHILE_TRANSFER_SENDER,
        read_fixture("tests/banks/banco_chile/transference_subject.txt"),
        read_fixture("tests/banks/banco_chile/transference.txt"),
    )

    response = post_email(client, raw, user.ingest_token)

    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    with Session(engine) as session:
        assert len(session.exec(select(DbTransference)).all()) == 1


def test_ingest_bad_signature_rejected(client, engine):
    user = make_user(engine)
    raw = build_raw_email(BANCO_CHILE_PURCHASE_SENDER, "Cargo en cuenta", "body")

    response = client.post(
        f"/ingest/email?recipient=u-{user.ingest_token}@in.finitum.app",
        content=raw,
        headers={"X-Finitum-Signature": "sha256=deadbeef"},
    )

    assert response.status_code == 401
    with Session(engine) as session:
        assert session.exec(select(DbExpense)).all() == []


def test_ingest_unknown_token_returns_200_without_persisting(client, engine):
    make_user(engine)
    raw = build_raw_email(
        BANCO_CHILE_PURCHASE_SENDER,
        read_fixture("tests/banks/banco_chile/purchase_subject.txt"),
        read_fixture("tests/banks/banco_chile/purchase_clp.txt"),
    )

    response = post_email(client, raw, "nonexistenttoken")

    assert response.status_code == 200
    assert response.json()["status"] == "unknown_token"
    with Session(engine) as session:
        assert session.exec(select(DbExpense)).all() == []


def test_ingest_duplicate_message_id_dropped(client, engine):
    user = make_user(engine)
    raw = build_raw_email(
        BANCO_CHILE_PURCHASE_SENDER,
        read_fixture("tests/banks/banco_chile/purchase_subject.txt"),
        read_fixture("tests/banks/banco_chile/purchase_clp.txt"),
        message_id="<dupe@bank>",
    )

    first = post_email(client, raw, user.ingest_token)
    second = post_email(client, raw, user.ingest_token)

    assert first.json()["status"] == "saved"
    assert second.json()["status"] == "duplicate"
    with Session(engine) as session:
        assert len(session.exec(select(DbExpense)).all()) == 1


def test_ingest_foreign_sender_ignored(client, engine):
    user = make_user(engine)
    raw = build_raw_email(
        "spam@malicious.com",
        read_fixture("tests/banks/banco_chile/purchase_subject.txt"),
        read_fixture("tests/banks/banco_chile/purchase_clp.txt"),
    )

    response = post_email(client, raw, user.ingest_token)

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    with Session(engine) as session:
        assert session.exec(select(DbExpense)).all() == []


def test_ingest_forwarding_confirmation_captured(client, engine):
    user = make_user(engine)
    body = (
        "Banco de Chile has requested to automatically forward mail to your address.\n"
        "Confirmation code: 123456789\n"
        "Please click the link below to confirm:\n"
        "https://mail.google.com/mail/vf-%5B...%5D-abcdef\n"
    )
    raw = build_raw_email("Gmail Team <forwarding-noreply@google.com>", "Forwarding Confirmation", body)

    response = post_email(client, raw, user.ingest_token)
    assert response.status_code == 200
    assert response.json()["status"] == "confirmation"

    # The authenticated confirmation endpoint surfaces it for the frontend.
    confirmation = server.ingest.get_confirmation(client.fake_redis, user.ingest_token)
    assert confirmation is not None
    assert confirmation.get("code") == "123456789"


def test_get_ingest_address_generates_token(engine):
    """GET /ingest/address lazily allocates a token for a user without one."""
    with Session(engine) as session:
        user = User(username="noaddr", email="noaddr@example.com", bank="banco_chile")
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

    # Drive the endpoint logic directly (auth dependency needs a JWT otherwise).
    from db.models import User as UserModel

    with Session(engine) as session:
        u = session.exec(select(UserModel).where(UserModel.id == user_id)).one()
        result = server.get_ingest_address(current_user=u, session=session)
    assert "u-" in result.body.decode()
