from parsers.transference import Transference
from db.models import Expense as DBExpense, Transference as DBTransference
from parsers.expense import Expense


def expense_to_db_model(expense: Expense) -> DBExpense:
    """Convert to database model"""
    from db.models import Expense as DBExpense

    return DBExpense(
        commerce=expense.commerce,
        amount=expense.value,
        currency=expense.currency,
        category=expense.category,
        date=expense.date,
        description="Extracted from email",
    )


def transference_to_db_model(transference: Transference) -> DBTransference:
    """Convert to database model"""

    return DBTransference(
        recipient=transference.recipient,
        amount=transference.value,
        currency=transference.currency,
        category=transference.category,
        date=transference.date,
        description="Extracted from email",
    )

