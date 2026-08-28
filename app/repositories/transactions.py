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
    stmt = stmt.order_by(transaction.transaction_id.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


# Descriptions mix both languages ("Mercado Livre", "Netflix subscription"), so each side of
# the match concatenates one expression per config: a word stemmed by either dictionary hits,
# and a stopword in one language still survives through the other. Adding a language here means
# recreating the GIN index in migration 766fc8d9b55a with the same expression.
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
        t.value                                                      AS total_value,
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
        END                                                          AS installment_value
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
    if due_date_from is not None:
        conditions.append("due_date >= :due_date_from")
        params["due_date_from"] = due_date_from
    if due_date_to is not None:
        conditions.append("due_date <= :due_date_to")
        params["due_date_to"] = due_date_to

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    result = db.execute(
        text(f"""
            SELECT * FROM ({CREDIT_INSTALLMENTS_SQL}) installments
            {where_clause}
            ORDER BY transaction_id, installment_number
            OFFSET :skip LIMIT :limit
        """),
        params,
    )
    return list(result.mappings().all())


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

