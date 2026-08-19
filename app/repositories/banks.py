from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.models import banks

def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    bank_id: int | None = None,
    bank_name: str | None = None,
) -> list[banks]:
    stmt = select(banks)
    if bank_name is not None:
        stmt = stmt.where(banks.bank_name.ilike(f"%{bank_name}%"))
    if bank_id is not None:
        stmt = stmt.where(banks.bank_id == bank_id)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def create(db: Session, data: dict) -> banks:
    obj = banks(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: banks, data: dict) -> banks:
    for key, value in data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: banks) -> None:
    db.delete(obj)
    db.commit()

