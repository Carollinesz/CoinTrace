from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    transaction_id: int | None = None,
    account_id: int | None = None,
    category: str | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
) -> list:
    conditions = []
    params: dict = {"skip": skip, "limit": limit}

    if transaction_id is not None:
        conditions.append("transaction_id = :transaction_id")
        params["transaction_id"] = transaction_id
    if account_id is not None:
        conditions.append("account_id = :account_id")
        params["account_id"] = account_id
    if category is not None:
        conditions.append("category ILIKE :category")
        params["category"] = f"%{category}%"
    if due_date_from is not None:
        conditions.append("due_date >= :due_date_from")
        params["due_date_from"] = due_date_from
    if due_date_to is not None:
        conditions.append("due_date <= :due_date_to")
        params["due_date_to"] = due_date_to

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    result = db.execute(
        text(f"""
            SELECT * FROM credit_installments_view
            {where_clause}
            ORDER BY transaction_id, installment_number
            OFFSET :skip LIMIT :limit
        """),
        params,
    )
    return result.mappings().all()
