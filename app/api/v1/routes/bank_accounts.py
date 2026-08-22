from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import BankAccountCreate, BankAccountRead, BankAccountUpdate
from app.services import bank_accounts as service

router = APIRouter(prefix="/bank-accounts", tags=["bank-accounts"])


@router.get("", response_model=list[BankAccountRead])
def handle_list_bank_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    bank_id: int | None = Query(None),
    account_name: str | None = Query(None),
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list(db, skip=skip, limit=limit, bank_id=bank_id, account_name=account_name, account_type=account_type)



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
