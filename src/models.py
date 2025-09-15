from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from parse import Currency, ExpenseCategory


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
