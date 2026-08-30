from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import fixed_expense
from app.repositories import bank_accounts as bank_accounts_repo
from app.repositories import fixed_expenses, transactions, bank_accounts
from app.schemas.schemas import (
    CurrentExpensesRead,
    FixedExpenseCreate,
    FixedExpenseUpdate,
    MonthlyBalanceRead,
)


def _ensure_account_exists(db: Session, account_id: int) -> None:
    if not bank_accounts_repo.list_all(db, skip=0, limit=1, account_id=account_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank account {account_id} not found",
        )


# Every credit due date must be read, not a page of them, so the repository limit is raised
# past any realistic instalment horizon (the default 100 covers only ~8 years of months).
_ALL_DUE_DATES = 10_000


def money_after_all_expenses(db: Session) -> list[MonthlyBalanceRead]:
    """Money left in each month covered by credit instalments.

    Fixed expenses and the current balance are the same for every month; only the credit
    instalments falling due change, so each month stands on its own with no carry-over.
    """
    monthly_fixed = fixed_expenses.current_spending(db)
    credit_by_month = _sum_credit_by_month(transactions.list_credit_by_due_date(db, limit=_ALL_DUE_DATES))
    current_money = bank_accounts.list_current_total_money(db)
    return [
        _month_balance(year, month, credit_by_month[(year, month)], monthly_fixed, current_money)
        for year, month in sorted(credit_by_month)
    ]


def _sum_credit_by_month(rows: list) -> dict[tuple[int, int], Decimal]:
    # Rows are grouped by due_date, so cards with different due days land on the same month.
    totals: dict[tuple[int, int], Decimal] = {}
    for row in rows:
        key = (int(row["year"]), int(row["month"]))
        totals[key] = totals.get(key, Decimal(0)) + row["value"]
    return totals


def _month_balance(
    year: int,
    month: int,
    credit: Decimal,
    monthly_fixed: Decimal,
    current_money: Decimal,
) -> MonthlyBalanceRead:
    total = credit + monthly_fixed
    return MonthlyBalanceRead(
        year=year,
        month=month,
        credit_expenses=credit,
        fixed_expenses=monthly_fixed,
        total_expenses=total,
        balance=current_money - total,
    )


def handle_get(db: Session, expense_id: int) -> fixed_expense:
    matches = fixed_expenses.list_all(db, skip=0, limit=1, expense_id=expense_id)
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fixed expense {expense_id} not found",
        )
    return matches[0]


def handle_list(
    db: Session,
    skip: int,
    limit: int,
    expense_id: int | None = None,
    account_id: int | None = None,
    category: str | None = None,
    is_active: bool | None = None,
) -> list[fixed_expense]:
    return fixed_expenses.list_all(db, skip=skip, limit=limit, expense_id=expense_id, account_id=account_id, category=category, is_active=is_active)


def current_spending(db: Session) -> CurrentExpensesRead:
    return CurrentExpensesRead(value=fixed_expenses.current_spending(db))

def handle_create(db: Session, payload: FixedExpenseCreate) -> fixed_expense:
    if payload.account_id is not None:
        _ensure_account_exists(db, payload.account_id)
    return fixed_expenses.create(db, payload.model_dump())


_UPDATABLE_FIELDS = {"name", "value", "due_day", "category", "account_id", "is_active"}


def handle_update(db: Session, expense_id: int, payload: FixedExpenseUpdate) -> fixed_expense:
    obj = handle_get(db, expense_id)
    data = payload.model_dump(exclude_unset=True)

    if "account_id" in data and data["account_id"] is not None:
        _ensure_account_exists(db, data["account_id"])

    merged = {field: data.get(field, getattr(obj, field)) for field in _UPDATABLE_FIELDS}
    return fixed_expenses.update(db, obj, merged)


def handle_delete(db: Session, expense_id: int) -> None:
    obj = handle_get(db, expense_id)
    fixed_expenses.delete(db, obj)
