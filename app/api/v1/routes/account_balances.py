from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import BankAccountBalanceRead
from app.services import account_balances as service

router = APIRouter(prefix="/account-balances", tags=["views"])


@router.get("", response_model=list[BankAccountBalanceRead])
def handle_list_account_balances(
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list(db, account_type=account_type)

