from parsers.transference import Transference
from db.models import Expense as DBExpense, Transference as DBTransference
from parsers.expense import Expense


def expense_to_db_model(expense: Expense, category_id: int) -> DBExpense:
    """Convert to database model"""
    from db.models import Expense as DBExpense

    return DBExpense(
        commerce=expense.commerce,
        amount=expense.value,
        currency=expense.currency,
        category_id=category_id,
        date=expense.date,
        description="Extracted from email",
    )


def transference_to_db_model(transference: Transference, category_id: int) -> DBTransference:
    """Convert to database model"""

    return DBTransference(
        recipient=transference.recipient,
        amount=transference.value,
        currency=transference.currency,
        category_id=category_id,
        date=transference.date,
        description="Extracted from email",
    )
