from datetime import datetime
import json
from typing import Any, ClassVar, Optional

from google.oauth2.credentials import Credentials
from db.service import get_session
from utils.logger import get_logger

from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel, select, or_, Text, Column
from parsers.base import Currency, ExpenseCategory

from pwdlib import PasswordHash

pwd_context = PasswordHash.recommended()
logger = get_logger()


def minimum_date_factory() -> datetime:
    return datetime(year=2025, month=1, day=1)


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str | None = Field(default=None)
    email: EmailStr = Field(unique=True, index=True)
    last_update: datetime = Field(default_factory=minimum_date_factory)
    google_credentials: Optional["UserGoogleCredential"] = Relationship(back_populates="user")

    def set_password(self, password: str) -> None:
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        if not self.password:
            return False
        return pwd_context.verify(password, self.password)

    @classmethod
    def create(cls, username: str, email: str, password: str) -> "User":
        user = cls(username=username, email=email)
        user.set_password(password)
        return user

    @classmethod
    def get_user(cls, username: str) -> "User | None":
        with next(get_session()) as session:
            return session.exec(select(User).where(or_(User.email == username, User.username == username))).first()


class UserGoogleCredential(SQLModel, table=True):
    __tablename__ = "user_google_credentials"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    user: "User" = Relationship(back_populates="google_credentials", sa_relationship_kwargs={"uselist": False})

    token: str | None = Field(default=None, sa_column=Column(Text))  # access token (optional to persist)
    refresh_token: str = Field(sa_column=Column(Text))  # long
    token_uri: str = Field(sa_column=Column(Text))
    client_id: str = Field(sa_column=Column(Text))
    client_secret: str = Field(sa_column=Column(Text))

    # store JSON arrays as TEXT; parse on load/save
    scopes_json: str = Field(sa_column=Column(Text))
    granted_scopes_json: str = Field(sa_column=Column(Text))

    expiry: datetime | None = None
    id_token: str | None = Field(default=None, sa_column=Column(Text))

    def scopes(self) -> list[str]:
        try:
            v = json.loads(self.scopes_json)
            return v if isinstance(v, list) else []
        except Exception:
            return []

    def granted_scopes(self) -> list[str]:
        try:
            v = json.loads(self.granted_scopes_json)
            return v if isinstance(v, list) else []
        except Exception:
            return []


class Expense(SQLModel, table=True):
    __tablename__ = "expenses"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    commerce: str = Field(index=True)
    amount: float = Field()
    currency: Currency = Field(default=Currency.CLP)
    category: ExpenseCategory = Field(default=ExpenseCategory.GENERAL)
    date: datetime = Field(default_factory=datetime.now)
    description: str | None = Field(default=None)


class Transference(SQLModel, table=True):
    __tablename__ = "transferences"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    recipient: str = Field(index=True)
    amount: float = Field()
    currency: Currency = Field(default=Currency.CLP)
    category: ExpenseCategory = Field(default=ExpenseCategory.GENERAL)
    date: datetime = Field(default_factory=datetime.now)
    description: str | None = Field(default=None)


class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        min_len = 8
        if len(v) < min_len:
            msg = "Password must be at least 8 characters"
            raise ValueError(msg)
        return v


class UserLogin(SQLModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str

    @field_validator("username", "email")
    @classmethod
    def validate_user_identifier(cls, v: str, values: dict[str, str]) -> str:
        # Ensure at least one identifier is provided
        if not v and not values.get("email") and not values.get("username"):
            msg = "Either email or username must be provided"
            raise ValueError(msg)
        return v


class UserResponse(SQLModel):
    id: int
    username: str
    email: EmailStr
    last_update: datetime

    model_config: ClassVar[dict[str, Any]] = {"from_attributes": True}  # type: ignore[assignment]


class UserLoginResponse(SQLModel):
    user: UserResponse
    access_token: str
    token_type: str


class UpdateError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def update_or_create_user(user_data: User) -> None:
    from db.service import get_session

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


def _normalize_scopes(scopes_val: list | str | None) -> list[str]:
    import json

    if scopes_val is None:
        return []
    if isinstance(scopes_val, list):
        return [s for s in scopes_val if isinstance(s, str)]
    if isinstance(scopes_val, str):
        # Try JSON first; if not JSON, try comma-splitting; finally treat as single scope
        try:
            v = json.loads(scopes_val)
            if isinstance(v, list):
                return [s for s in v if isinstance(s, str)]
        except Exception:
            logger.error("Cannot load scopes from json, trying to load as string")
        if "," in scopes_val:
            return [s.strip() for s in scopes_val.split(",") if s.strip()]
        return [scopes_val.strip()]
    return []


def rebuild_credentials(credentials: dict[str, Any] | UserGoogleCredential) -> Credentials:
    from datetime import datetime
    from google.oauth2.credentials import Credentials

    if isinstance(credentials, dict):
        token_uri = credentials.get("token_uri")
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
        refresh_token = credentials.get("refresh_token")
        token = credentials.get("token")
        scopes = _normalize_scopes(credentials.get("scopes") or credentials.get("granted_scopes"))
        id_token = credentials.get("id_token")
        expiry = credentials.get("expiry")
        if isinstance(expiry, str):
            try:
                expiry = datetime.fromisoformat(expiry)
            except Exception:
                expiry = None
    else:
        token_uri = credentials.token_uri
        client_id = credentials.client_id
        client_secret = credentials.client_secret
        refresh_token = credentials.refresh_token
        token = credentials.token
        scopes = credentials.scopes() or credentials.granted_scopes()
        id_token = credentials.id_token
        expiry = credentials.expiry

    if not refresh_token:
        raise ValueError("Missing refresh_token; cannot rebuild Credentials")

    return Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes or None,
        id_token=id_token,
        expiry=expiry,
    )
