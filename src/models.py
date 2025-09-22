from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, ForeignKey, SQLModel
from parse import Currency, ExpenseCategory

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def minimum_date_factory() -> datetime:
    return datetime(year=2025, month=1, day=1)


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str = Field()
    email: EmailStr = Field(unique=True, index=True)

    def set_password(self, password: str):
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password)


class UserMetadata(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user: ForeignKey[User] = ForeignKey("User")
    last_update: datetime = Field(default_factory=minimum_date_factory)


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
