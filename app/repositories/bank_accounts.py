from sqlalchemy import select, text, func
from sqlalchemy.orm import Session
from app.schemas.schemas import BankAccountCreate
from app.models.models import bank_account, transaction

def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    account_id: int | None = None,
    bank_id: int | None = None,
    account_name: str | None = None,
    account_type: str | None = None,
) -> list[bank_account]:
    stmt = select(bank_account)
    if account_id is not None:
        stmt = stmt.where(bank_account.account_id == account_id)
    if bank_id is not None:
        stmt = stmt.where(bank_account.bank_id == bank_id)
    if account_name is not None:
        stmt = stmt.where(bank_account.account_name.ilike(f"%{account_name}%"))
    if account_type is not None:
        stmt = stmt.where(bank_account.account_type.ilike(f"%{account_type}%"))
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())

def list_all_balances(
    db: Session,
    account_id: int | None = None,
    account_type: str | None = None,
) -> list:
    conditions = []
    params: dict = {}

    if account_id is not None:
        conditions.append("ba.account_id = :account_id")
        params["account_id"] = account_id
    if account_type is not None:
        conditions.append("ba.account_type = :account_type")
        params["account_type"] = account_type

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    result = db.execute(
        text(f"""

            SELECT
                ba.account_id,
                ba.account_name,
                ba.account_type,
                COALESCE(ba.start_value, 0)                                                              AS start_value,
                COALESCE(SUM(t.value) FILTER (WHERE t.tracking = true AND t.value > 0), 0)              AS total_gains,
                COALESCE(SUM(ABS(t.value)) FILTER (WHERE t.tracking = true AND t.value < 0), 0)         AS total_expenses,
                COALESCE(ba.start_value, 0)
                    + COALESCE(SUM(t.value) FILTER (WHERE t.tracking = true AND t.value > 0), 0)
                    - COALESCE(SUM(ABS(t.value)) FILTER (WHERE t.tracking = true AND t.value < 0), 0)   AS current_balance
            FROM bank_accounts ba
            LEFT JOIN transactions t ON t.account_id = ba.account_id
            {where_clause}
            GROUP BY ba.account_id, ba.account_name, ba.account_type, ba.start_value
        
        """),
        params,
    )
    return result.mappings().all()

def list_earnings(
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
    ).where(transaction.value > 0).where(transaction.tracking.is_(True))

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


def create(db: Session, data: dict) -> bank_account:
    obj = bank_account(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: bank_account, data: dict) -> bank_account:
    for key, value in data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: bank_account) -> None:
    db.delete(obj)
    db.commit()
