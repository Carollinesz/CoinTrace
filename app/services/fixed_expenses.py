from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import fixed_expense
from app.repositories import bank_accounts as bank_accounts_repo
from app.repositories import fixed_expenses as repo
from app.schemas.schemas import FixedExpenseCreate, FixedExpenseUpdate


def _ensure_account_exists(db: Session, account_id: int) -> None:
    if not bank_accounts_repo.list_all(db, skip=0, limit=1, account_id=account_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank account {account_id} not found",
        )


def handle_get(db: Session, expense_id: int) -> fixed_expense:
    matches = repo.list_all(db, skip=0, limit=1, expense_id=expense_id)
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
    return repo.list_all(db, skip=skip, limit=limit, expense_id=expense_id, account_id=account_id, category=category, is_active=is_active)


def handle_create(db: Session, payload: FixedExpenseCreate) -> fixed_expense:
    if payload.account_id is not None:
        _ensure_account_exists(db, payload.account_id)
    return repo.create(db, payload.model_dump())


_UPDATABLE_FIELDS = {"name", "value", "due_day", "category", "account_id", "is_active"}


def handle_update(db: Session, expense_id: int, payload: FixedExpenseUpdate) -> fixed_expense:
    obj = handle_get(db, expense_id)
    data = payload.model_dump(exclude_unset=True)

    if "account_id" in data and data["account_id"] is not None:
        _ensure_account_exists(db, data["account_id"])

    merged = {field: data.get(field, getattr(obj, field)) for field in _UPDATABLE_FIELDS}
    return repo.update(db, obj, merged)


def handle_delete(db: Session, expense_id: int) -> None:
    obj = handle_get(db, expense_id)
    repo.delete(db, obj)
