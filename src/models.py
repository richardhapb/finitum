from datetime import datetime
from typing import Any, ClassVar, Optional

from google.oauth2.credentials import Credentials
from database import get_session
from utils import get_logger

from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel, select
from parse import Currency, ExpenseCategory

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger()


def minimum_date_factory() -> datetime:
    return datetime(year=2025, month=1, day=1)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: Optional[str] = Field(default=None)
    email: EmailStr = Field(unique=True, index=True)
    last_update: datetime = Field(default_factory=minimum_date_factory)
    google_credentials: Optional["UserGoogleCredentials"] = Relationship(back_populates="user")

    def set_password(self, password: str):
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password)

    @classmethod
    def create(cls, username: str, email: str, password: str) -> "User":
        user = cls(username=username, email=email)
        user.set_password(password)
        return user


class UserGoogleCredentials(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="google_credentials")
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


class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(SQLModel):
    id: int
    username: str
    email: EmailStr
    last_update: datetime

    model_config: ClassVar[dict[str, Any]] = {"orm_mode": True}  # type: ignore[assignment]


class UpdateError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def update_or_create_user(user_data: User) -> None:
    with next(get_session()) as session:
        # Check if user exists
        statement = select(User).where(User.email == user_data.email)
        existing_user = session.exec(statement).first()

        if existing_user:
            # Update existing user
            for key, val in user_data.__dict__.items():
                if key != "_sa_instance_state" and hasattr(existing_user, key):
                    setattr(existing_user, key, val)
            logger.info("Updated user: %s", user_data.email)
        else:
            # Create new user
            session.add(user_data)
            logger.info("Created user: %s", user_data.email)

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
