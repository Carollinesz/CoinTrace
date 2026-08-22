from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import fixed_expense

def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    account_id: int | None = None,
    category: str | None = None,
    is_active: bool | None = None,
) -> list[fixed_expense]:
    stmt = select(fixed_expense)
    if account_id is not None:
        stmt = stmt.where(fixed_expense.account_id == account_id)
    if category is not None:
        stmt = stmt.where(fixed_expense.category.ilike(f"%{category}%"))
    if is_active is not None:
        stmt = stmt.where(fixed_expense.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def create(db: Session, data: dict) -> fixed_expense:
    obj = fixed_expense(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: fixed_expense, data: dict) -> fixed_expense:
    for key, value in data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: fixed_expense) -> None:
    db.delete(obj)
    db.commit()
