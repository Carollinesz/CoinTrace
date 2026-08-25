import pandas as pd
from datetime import date
from ofxparse import OfxParser

from functools import reduce

from sqlalchemy import func, literal_column, select
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

