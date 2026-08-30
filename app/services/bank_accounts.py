from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import bank_account
from app.repositories import bank_accounts as repo
from app.schemas.schemas import BankAccountCreate, BankAccountUpdate,  CurrentBalanceRead

_MAX_LOOKUP = 500  # matches the highest `limit` the endpoints accept


def _find_by_name(db: Session, account_name: str) -> bank_account | None:
    matches = repo.list_all(db, skip=0, limit=_MAX_LOOKUP, account_name=account_name)
    return next((obj for obj in matches if obj.account_name == account_name), None)


def handle_get(db: Session, account_id: int) -> bank_account:
    matches = repo.list_all(db, skip=0, limit=1, account_id=account_id)
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Accound {account_id} not found",
        )
    return matches[0]


def handle_list(
    db: Session,
    skip: int,
    limit: int,
    account_id: int | None = None,
    bank_id: int | None = None,
    account_name: str | None = None,
    account_type: str | None = None,
) -> list[bank_account]:
    return repo.list_all(db, skip=skip, limit=limit, account_id=account_id, bank_id=bank_id, account_name=account_name, account_type=account_type)

def handle_list_balances(
    db: Session,
    account_id: int | None = None,
    account_name: str | None = None,
    account_type: str | None = None,
) -> list:
    return repo.list_all_balances(db, account_id=account_id, account_type=account_type, account_name=account_name)


def handle_list_current_balance(db: Session) -> CurrentBalanceRead:
    return CurrentBalanceRead(current_balance=repo.list_current_total_money(db))

def handle_list_earnings(
    db: Session,
    account_id: int | None,
    account_name: str | None,
    category: str | None,
    year_transaction: int | None,
    month_transaction: int | None,
) -> list:
    return repo.list_earnings(
        db,
        account_id=account_id,
        account_name=account_name, 
        category=category, 
        year_transaction=year_transaction, 
        month_transaction=month_transaction)



def handle_create(db: Session, payload: BankAccountCreate) -> bank_account:
    if _find_by_name(db, payload.account_name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account name '{payload.account_name}' already exists",
        )
    return repo.create(db, payload.model_dump())


def handle_update(
    db: Session, account_id: int, payload: BankAccountUpdate
) -> bank_account:
    obj = handle_get(db, account_id)
    data = payload.model_dump(exclude_unset=True)



    if "account_name" in data and data["account_name"] != obj.account_name:
        if _find_by_name(db, data["account_name"]) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account name is already used '{data['account_name']}' already exists",
            )
    return repo.update(db, obj, data)


def handle_delete(db: Session, account_id: int) -> None:
    obj = handle_get(db, account_id)
    repo.delete(db, obj)
