from datetime import date

from sqlalchemy.orm import Session

from app.repositories import credit_installments as repo


def handle_list(
    db: Session,
    skip: int,
    limit: int,
    transaction_id: int | None = None,
    account_id: int | None = None,
    category: str | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
) -> list:
    return repo.list_all(
        db,
        skip=skip,
        limit=limit,
        transaction_id=transaction_id,
        account_id=account_id,
        category=category,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
    )
