import os
from datetime import datetime, UTC
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
    """Default to now - new users won't fetch historical emails."""
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str | None = Field(default=None)
    email: EmailStr = Field(unique=True, index=True)
    bank: str = Field(default="banco_chile")
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

    token: str | None = Field(default=None, sa_column=Column(Text))  # access token (optional to persist), encrypted
    refresh_token: str = Field(sa_column=Column(Text))  # long, encrypted
    token_uri: str = Field(sa_column=Column(Text))
    client_id: str = Field(sa_column=Column(Text))

    # store JSON arrays as TEXT; parse on load/save
    scopes_json: str = Field(sa_column=Column(Text))
    granted_scopes_json: str = Field(sa_column=Column(Text))

    expiry: datetime | None = None
    id_token: str | None = Field(default=None, sa_column=Column(Text))
    is_valid: bool = Field(default=True)  # False when refresh token expired/revoked

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
    category_id: int = Field(foreign_key="categories.id", index=True)
    date: datetime = Field(default_factory=minimum_date_factory)
    description: str | None = Field(default=None)


class Transference(SQLModel, table=True):
    __tablename__ = "transferences"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    recipient: str = Field(index=True)
    amount: float = Field()
    currency: Currency = Field(default=Currency.CLP)
    category: ExpenseCategory = Field(default=ExpenseCategory.GENERAL)
    date: datetime = Field(default_factory=minimum_date_factory)
    description: str | None = Field(default=None)


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int | None = Field(default=None, primary_key=True)
    # If it is not associated to an user, is a global category
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    slug: str = Field(index=True, unique=True)
    name_en: str
    name_es: str


class CategoryPattern(SQLModel, table=True):
    __tablename__ = "category_patterns"

    id: int | None = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="categories.id")
    pattern: str


class CategoryCreate(SQLModel):
    name: str
    pattern: str | None = None


class CategoryRead(SQLModel):
    id: int
    slug: str
    name: str
    name_en: str
    name_es: str
    is_custom: bool
    patterns: list[str] = []

    model_config: ClassVar[dict[str, Any]] = {"from_attributes": True}


class ExpenseCreate(SQLModel):
    """Model for creating a new expense via API."""

    commerce: str
    amount: float
    currency: Currency = Currency.CLP
    category_id: int
    date: datetime | None = None
    description: str | None = None


class ExpenseRead(SQLModel):
    id: int
    user_id: int
    commerce: str
    amount: float
    currency: Currency
    category_id: int
    category_slug: str
    category_name: str
    category_is_custom: bool
    date: datetime
    description: str | None = None


class TransferenceRead(SQLModel):
    id: int
    user_id: int
    recipient: str
    amount: float
    currency: Currency
    category: ExpenseCategory
    category_slug: str
    category_name: str
    date: datetime
    description: str | None = None


class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str
    bank: str = "banco_chile"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        min_len = 8
        if len(v) < min_len:
            msg = "Password must be at least 8 characters"
            raise ValueError(msg)
        return v


class UserUpdate(SQLModel):
    """Model for updating user profile."""

    username: str | None = None
    bank: str | None = None


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
    has_google_credentials: bool = False
    is_google_credentials_valid: bool = False

    model_config: ClassVar[dict[str, Any]] = {"from_attributes": True}


class UserLoginResponse(SQLModel):
    user: UserResponse


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
    if isinstance(credentials, UserGoogleCredential) and not credentials.is_valid:
        raise ValueError("Credentials are marked as invalid")

    def _to_naive_utc(dt: datetime | None) -> datetime | None:
        """Convert datetime to naive UTC for Google's auth library compatibility.

        Google's auth library compares expiry against _helpers.utcnow() which
        returns a naive datetime. We must provide a naive UTC datetime to avoid
        'can't compare offset-naive and offset-aware datetimes' errors.
        """
        if not dt:
            return None
        if dt.tzinfo is None:
            # Already naive, assume it's UTC
            return dt
        # Convert to UTC and strip tzinfo for naive comparison
        return dt.astimezone(UTC).replace(tzinfo=None)

    def _to_scopes(sc: str | None) -> list[str] | None:
        if not sc:
            return None
        if isinstance(sc, str):
            # accept comma/space separated
            parts = [s for s in (p.strip() for p in sc.replace(",", " ").split()) if s]
            return parts or None
        return None

    token_uri = getattr(credentials, "token_uri", None) or "https://oauth2.googleapis.com/token"
    client_id = getattr(credentials, "client_id", None) or os.environ.get("GOOGLE_CLIENT")
    client_secret = getattr(credentials, "client_secret", None) or os.environ.get("GOOGLE_SECRET")
    refresh_token = getattr(credentials, "refresh_token", None)
    token = getattr(credentials, "token", None)
    sc_attr = getattr(credentials, "scopes", None)
    scopes = _to_scopes(sc_attr or getattr(credentials, "granted_scopes", None))
    id_token = getattr(credentials, "id_token", None)

    # Stored credentials persist token/refresh_token/id_token encrypted at rest.
    if isinstance(credentials, UserGoogleCredential):
        from utils.crypto import decrypt

        refresh_token = decrypt(refresh_token)
        token = decrypt(token)
        id_token = decrypt(id_token)
    expiry = _to_naive_utc(getattr(credentials, "expiry", None))

    missing = [
        name
        for name, val in [
            ("refresh_token", refresh_token),
            ("client_id", client_id),
            ("client_secret", client_secret),
            ("token_uri", token_uri),
        ]
        if not val
    ]
    if missing:
        msg = f"Missing OAuth fields for refresh: {', '.join(missing)}"
        raise ValueError(msg)

    return Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
        id_token=id_token,
        expiry=expiry,
    )
