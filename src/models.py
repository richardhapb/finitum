from datetime import datetime
from typing import Optional

from google.oauth2.credentials import Credentials
from database import get_session
from utils import get_logger

from pydantic import EmailStr
from sqlmodel import Field, ForeignKey, SQLModel, select
from parse import Currency, ExpenseCategory

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger()


def minimum_date_factory() -> datetime:
    return datetime(year=2025, month=1, day=1)


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str = Field()
    email: EmailStr = Field(unique=True, index=True)
    last_update: datetime = Field(default_factory=minimum_date_factory)

    def set_password(self, password: str):
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password)


class UserGoogleCredentials(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user: ForeignKey[User] = ForeignKey("User")
    token: str = Field(max_length=255)
    refresh_token: str = Field(max_length=255)
    granted_scopes: str = Field()

    def __getitem__(self, name: str):
        return getattr(self, name)


class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    commerce: str = Field(index=True)
    amount: float = Field()
    currency: Currency = Field(default=Currency.CLP)
    category: ExpenseCategory = Field(default=ExpenseCategory.GENERAL)
    date: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = Field(default=None)


class Transference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recipient: str = Field(index=True)
    amount: float = Field()
    currency: Currency = Field(default=Currency.CLP)
    category: ExpenseCategory = Field(default=ExpenseCategory.GENERAL)
    date: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = Field(default=None)


class UpdateError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def update_or_create_user(user_data: User) -> None:
    with next(get_session()) as session:
        # Check if hero with this email already exists
        statement = select(User).where(User.email == user_data.email)
        existing_hero = session.exec(statement).first()

        for key, val in user_data:
            setattr(existing_hero, key, val)

        if existing_hero:
            logger.info("Updated hero: %s", user_data.email)
            session.refresh(existing_hero)
        else:
            session.add(user_data)
            logger.info("Created hero: %s", user_data.email)

        session.commit()


def rebuild_credentials(credentials: dict[str, str | None] | UserGoogleCredentials) -> Credentials:
    from oauth.google_oauth import CLIENT_CONFIG

    client_config = CLIENT_CONFIG["web"]
    return Credentials(
        refresh_token=getattr(credentials, "refresh_token"),
        scopes=getattr(credentials, "granted_scopes"),
        token=getattr(credentials, "token"),
        client_id=client_config.get("client_id"),
        client_secret=client_config.get("client_secret"),
        token_uri=client_config.get("token_uri"),
    )
