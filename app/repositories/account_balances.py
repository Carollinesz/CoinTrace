from sqlalchemy import text
from sqlalchemy.orm import Session


def list_all(
    db: Session,
    account_id: int | None = None,
    account_type: str | None = None,
) -> list:
    conditions = []
    params: dict = {}

    if account_id is not None:
        conditions.append("account_id = :account_id")
        params["account_id"] = account_id
    if account_type is not None:
        conditions.append("account_type = :account_type")
        params["account_type"] = account_type

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    result = db.execute(
        text(f"SELECT * FROM bank_account_balance_view {where_clause} ORDER BY account_id"),
        params,
    )
    return result.mappings().all()
