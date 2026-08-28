from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import BankAccountCreate, BankAccountRead, BankAccountUpdate, BankAccountBalanceRead, BankAccountEarningsRead
from app.services import bank_accounts as service

router = APIRouter(prefix="/bank-accounts", tags=["bank-accounts"])


@router.get("", response_model=list[BankAccountRead])
def handle_list_bank_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    account_id: int | None = Query(None),
    bank_id: int | None = Query(None),
    account_name: str | None = Query(None),
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list(db, skip=skip, limit=limit, account_id=account_id, bank_id=bank_id, account_name=account_name, account_type=account_type)

@router.get("/account-balances", response_model=list[BankAccountBalanceRead])
def handle_list_account_balances(
    account_id: int | None = Query(None),
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list_balances(db, account_id=account_id, account_type=account_type)

@router.get("/account-earnings", response_model=list[BankAccountEarningsRead])
def handle_list_account_earnings(
    account_id: int | None = Query(None),
    category: str | None = Query(None),
    year_transaction: int | None = Query(None),
    month_transaction: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list_earnings(db, account_id=account_id, category=category, year_transaction=year_transaction, month_transaction=month_transaction)


@router.post("", response_model=BankAccountRead, status_code=status.HTTP_201_CREATED)
def handle_create_bank_account(
    payload: BankAccountCreate, db: Session = Depends(get_db)
):
    return service.handle_create(db, payload)


@router.patch("/{account_id}", response_model=BankAccountRead)
def handle_update_bank_account(
    account_id: int,
    payload: BankAccountUpdate,
    db: Session = Depends(get_db),
):
    return service.handle_update(db, account_id, payload)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def handle_delete_bank_account(account_id: int, db: Session = Depends(get_db)):
    service.handle_delete(db, account_id)
