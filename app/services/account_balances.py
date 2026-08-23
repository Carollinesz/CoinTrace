from sqlalchemy.orm import Session

from app.repositories import account_balances as repo


def handle_list(
    db: Session,
    account_id: int | None = None,
    account_type: str | None = None,
) -> list:
    return repo.list_all(db, account_id=account_id, account_type=account_type)
