from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import FixedExpenseCreate, FixedExpenseRead, FixedExpenseUpdate
from app.services import fixed_expenses as service

router = APIRouter(prefix="/fixed-expenses", tags=["fixed-expenses"])


@router.get("", response_model=list[FixedExpenseRead])
def handle_list_fixed_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    expense_id: int | None = Query(None),
    account_id: int | None = Query(None),
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list(db, skip=skip, limit=limit, expense_id=expense_id, account_id=account_id, category=category, is_active=is_active)


@router.post("", response_model=FixedExpenseRead, status_code=status.HTTP_201_CREATED)
def handle_create_fixed_expense(payload: FixedExpenseCreate, db: Session = Depends(get_db)):
    return service.handle_create(db, payload)


@router.patch("/{expense_id}", response_model=FixedExpenseRead)
def handle_update_fixed_expense(
    expense_id: int,
    payload: FixedExpenseUpdate,
    db: Session = Depends(get_db),
):
    return service.handle_update(db, expense_id, payload)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def handle_delete_fixed_expense(expense_id: int, db: Session = Depends(get_db)):
    service.handle_delete(db, expense_id)
