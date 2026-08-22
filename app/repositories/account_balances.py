from sqlalchemy import text
from sqlalchemy.orm import Session


def list_all(db: Session, account_type: str | None = None) -> list:
    params: dict = {}
    where_clause = ""
    if account_type is not None:
        where_clause = "WHERE account_type = :account_type"
        params["account_type"] = account_type
    result = db.execute(
        text(f"SELECT * FROM bank_account_balance_view {where_clause} ORDER BY account_id"),
        params,
    )
    return result.mappings().all()
