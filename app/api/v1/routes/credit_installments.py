from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import CreditInstallmentRead
from app.services import credit_installments as service

router = APIRouter(prefix="/credit-installments", tags=["views"])


@router.get("", response_model=list[CreditInstallmentRead])
def handle_list_credit_installments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    account_id: int | None = Query(None),
    category: str | None = Query(None),
    due_date_from: date | None = Query(None),
    due_date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list(
        db,
        skip=skip,
        limit=limit,
        account_id=account_id,
        category=category,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
    )

