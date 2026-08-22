import pandas as pd
from datetime import date
from ofxparse import OfxParser

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.models import transaction
from app.schemas.schemas import TransactionCreate

def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    account_id: int | None = None,
    type: str | None = None,
    category: str | None = None,
    tracking: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[transaction]:
    stmt = select(transaction)
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

