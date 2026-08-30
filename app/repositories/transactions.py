import pandas as pd
from datetime import date
from ofxparse import OfxParser

from functools import reduce

from sqlalchemy import func, literal_column, select, text
from sqlalchemy.orm import Session
from app.models.models import transaction
from app.schemas.schemas import TransactionCreate

def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    description: str | None = None,
    transaction_id: int | None = None,
    account_id: int | None = None,
    type: str | None = None,
    category: str | None = None,
    tracking: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[transaction]:
    stmt = select(transaction)
    if transaction_id is not None:
        stmt = stmt.where(transaction.transaction_id == transaction_id)
    if description is not None:
        stmt = stmt.where(_description_matches(description))
    if account_id is not None:
        stmt = stmt.where(transaction.account_id == account_id)
    if type is not None:
        stmt = stmt.where(transaction.type == type)
    if category is not None:
        stmt = stmt.where(transaction.category.ilike(f"%{category}%"))
    if tracking is not None:
        stmt = stmt.where(transaction.tracking == tracking)
    if date_from is not None:
        stmt = stmt.where(transaction.transaction_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(transaction.transaction_date <= date_to)
    stmt = stmt.order_by(transaction.transaction_date.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


SEARCH_CONFIGS = ("portuguese", "english")


def _description_matches(term: str):
    vector = _concat(
        func.to_tsvector(_regconfig(config), transaction.description)
        for config in SEARCH_CONFIGS
    )
    query = _concat(
        func.plainto_tsquery(_regconfig(config), term) for config in SEARCH_CONFIGS
    )
    return vector.bool_op("@@")(query)


def _concat(expressions):
    return reduce(lambda left, right: left.op("||")(right), expressions)


def _regconfig(config: str):
    # Rendered inline rather than bound, so the planner sees the same constant the index was
    # built with. Safe to interpolate: the values come from SEARCH_CONFIGS, never from input.
    return literal_column(f"'{config}'")


# Expands every credit transaction into one row per installment. Kept as raw SQL because the
# LATERAL generate_series has no concise ORM equivalent; it replaces the old
# credit_installments_view so the maths lives with the endpoint that serves it.
CREDIT_INSTALLMENTS_SQL = """
    SELECT
        t.transaction_id,
        t.account_id,
        t.description,
        t.category,
        t.transaction_date,
        t.value * -1                                                 AS total_value,
        (t.details->>'installments')::int                            AS total_installments,
        gs.n                                                         AS installment_number,
        (t.details->>'first_payment')::date
            + make_interval(months => gs.n - 1)                      AS due_date,
        COALESCE((t.details->>'interest')::numeric, 0)               AS interest_rate,
        CASE
            WHEN COALESCE((t.details->>'interest')::numeric, 0) = 0 THEN
                ROUND(t.value / (t.details->>'installments')::int, 4)
            ELSE
                ROUND(
                    t.value
                    * ((t.details->>'interest')::numeric
                       * POWER(1 + (t.details->>'interest')::numeric,
                               (t.details->>'installments')::int))
                    / (POWER(1 + (t.details->>'interest')::numeric,
                             (t.details->>'installments')::int) - 1),
                    4)
        END * -1                                                            AS installment_value
    FROM transactions t
    CROSS JOIN LATERAL generate_series(1, (t.details->>'installments')::int) AS gs(n)
    WHERE t.type = 'credit'
      AND t.details IS NOT NULL
      AND (t.details->>'installments') IS NOT NULL
      AND (t.details->>'first_payment') IS NOT NULL
"""


def list_credit_installments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    transaction_id: int | None = None,
    account_id: int | None = None,
    account_name: str | None = None,
    description: str | None = None,
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
    if description is not None:
        conditions.append(_description_matches_sql())
        params["description"] = description
    if category is not None:
        conditions.append("category ILIKE :category")
        params["category"] = f"%{category}%"
    if account_name is not None:
        conditions.append("account_name ILIKE :account_name")
        params["account_name"] = f"%{account_name}%"
    if due_date_from is not None:
        conditions.append("due_date >= :due_date_from")
        params["due_date_from"] = due_date_from
    if due_date_to is not None:
        conditions.append("due_date <= :due_date_to")
        params["due_date_to"] = due_date_to

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    result = db.execute(
        text(f"""
            SELECT ci.*, ba.account_name FROM ({CREDIT_INSTALLMENTS_SQL}) ci
            {where_clause}
            LEFT JOIN bank_accounts ba ON ci.account_id = ba.account_id
            ORDER BY installment_number ASC, due_date DESC
            OFFSET :skip LIMIT :limit
        """),
        params,
    )
    return list(result.mappings().all())


def list_credit_by_account(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    account_id: int | None = None,
    account_name:str | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    year: int | None = None,
    month: int | None = None
) -> list:
    conditions = []
    params: dict = {"skip": skip, "limit": limit}

    if account_id is not None:
        conditions.append("account_id = :account_id")
        params["account_id"] = account_id
    if account_name is not None:
        conditions.append("account_name = :account_name")
        params["account_name"] = account_name
    if due_date_from is not None:
        conditions.append("due_date >= :due_date_from")
        params["due_date_from"] = due_date_from
    if due_date_to is not None:
        conditions.append("due_date <= :due_date_to")
        params["due_date_to"] = due_date_to
    if year is not None:
        conditions.append("year = :year")
        params["year"] = year
    if month is not None:
        conditions.append("month = :month")
        params["month"] = month


    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    result = db.execute(
        text(f"""
            WITH credit_consolidate AS (
                SELECT 
                    ci.account_id, 
                    account_name, 
                    due_date, 
                    EXTRACT(year FROM due_date) AS year,  
                    EXTRACT(month FROM due_date) AS month,
                    SUM(installment_value) AS value 
                FROM ({CREDIT_INSTALLMENTS_SQL}) ci
                LEFT JOIN bank_accounts ba ON ci.account_id = ba.account_id
	            GROUP BY due_date, ci.account_id, account_name
            )
            SELECT 
                *
            FROM credit_consolidate
            {where_clause}
            ORDER BY due_date DESC, account_id ASC
            OFFSET :skip LIMIT :limit
        """),
        params,
    )
    return list(result.mappings().all())

def list_credit_by_due_date(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    year: int | None = None,
    month: int | None = None
) -> list:
    conditions = []
    params: dict = {"skip": skip, "limit": limit}

    if due_date_from is not None:
        conditions.append("due_date >= :due_date_from")
        params["due_date_from"] = due_date_from
    if due_date_to is not None:
        conditions.append("due_date <= :due_date_to")
        params["due_date_to"] = due_date_to
    if year is not None:
        conditions.append("year = :year")
        params["year"] = year
    if month is not None:
        conditions.append("month = :month")
        params["month"] = month


    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    result = db.execute(
        text(f"""
            WITH credit_consolidate AS (
                SELECT 
                    due_date, 
                    EXTRACT(year FROM due_date) AS year,  
                    EXTRACT(month FROM due_date) AS month,
                    SUM(installment_value) AS value 
                FROM ({CREDIT_INSTALLMENTS_SQL}) ci
                LEFT JOIN bank_accounts ba ON ci.account_id = ba.account_id
	            GROUP BY due_date
            )
            SELECT 
                *
            FROM credit_consolidate
            {where_clause}
            ORDER BY due_date DESC
            OFFSET :skip LIMIT :limit
        """),
        params,
    )
    return list(result.mappings().all())




def list_expenses_by_categorie(
    db: Session,
    account_id: int | None = None,
    category: str | None = None,
    year_transaction: int | None = None,
    month_transaction: int | None = None,
) -> list:
    stmt = select(
        transaction.year_transaction,
        transaction.month_transaction,
        transaction.account_id,
        transaction.category,
        func.sum(transaction.value).label("value"),
    ).where(transaction.value < 0).where(transaction.tracking.is_(True))

    if account_id is not None:
        stmt = stmt.where(transaction.account_id == account_id)
    if category is not None:
        stmt = stmt.where(transaction.category.ilike(f"%{category}%"))
    if year_transaction is not None:
        stmt = stmt.where(transaction.year_transaction == year_transaction)
    if month_transaction is not None:
        stmt = stmt.where(transaction.month_transaction == month_transaction)

    stmt = stmt.group_by(
                    transaction.year_transaction,
                    transaction.month_transaction,
                    transaction.account_id,
                    transaction.category) \
                .order_by(
                    transaction.year_transaction.desc(), 
                    transaction.month_transaction.asc(),
                    transaction.account_id.asc(),
                )
    return list(db.execute(stmt).mappings().all())



def _description_matches_sql() -> str:
    # Same expression as _description_matches, spelled in SQL so the raw installments query
    # keeps using the GIN index from migration 766fc8d9b55a.
    vector = " || ".join(
        f"to_tsvector('{config}', description)" for config in SEARCH_CONFIGS
    )
    query = " || ".join(
        f"plainto_tsquery('{config}', :description)" for config in SEARCH_CONFIGS
    )
    return f"({vector}) @@ ({query})"


def create(db: Session, data: dict) -> transaction:
    obj = transaction(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: transaction, data: dict) -> transaction:
    for key, value in data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: transaction) -> None:
    db.delete(obj)
    db.commit()


def bulk_create(db: Session, rows: list[dict]) -> list[transaction]:
    objs = [transaction(**row) for row in rows]
    db.add_all(objs)
    db.commit()
    for obj in objs:
        db.refresh(obj)
    return objs

