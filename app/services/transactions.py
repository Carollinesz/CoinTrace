import io
from decimal import Decimal, InvalidOperation

import pandas as pd
from fastapi import HTTPException, status
from ofxparse import OfxParser
from sqlalchemy.orm import Session
from datetime import date

from app.models.models import transaction
from app.repositories import bank_accounts as bank_accounts_repo
from app.repositories import transactions as repo
from app.schemas.schemas import TransactionCreate, TransactionUpdate, TransactionUploadResult, UploadRowError
from app.utils.text_functions import handle_normalize_text


def _ensure_account_exists(db: Session, account_id: int) -> None:
    if not bank_accounts_repo.list_all(db, skip=0, limit=1, account_id=account_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank account {account_id} not found",
        )


def _handle_not_found(transaction_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Transaction {transaction_id} not found",
    )


def handle_get(db: Session, transaction_id: int):
    """Row shaped for TransactionRead — carries the joined account_name."""
    matches = repo.list_all(db, skip=0, limit=1, transaction_id=transaction_id)
    if not matches:
        raise _handle_not_found(transaction_id)
    return matches[0]


def handle_get_entity(db: Session, transaction_id: int) -> transaction:
    """ORM entity, for the paths that update or delete the row."""
    obj = repo.get(db, transaction_id)
    if obj is None:
        raise _handle_not_found(transaction_id)
    return obj


def handle_list(
    db: Session,
    skip: int,
    limit: int,
    description: str | None = None,
    transaction_id: int | None = None,
    account_id: int | None = None,
    account_name: str | None = None,
    type: str | None = None,
    category: str | None = None,
    tracking: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list:
    return repo.list_all(
        db,
        skip=skip,
        limit=limit,
        description=description,
        transaction_id=transaction_id,
        account_id=account_id,
        account_name=account_name,
        type=type,
        category=category,
        tracking=tracking,
        date_from=date_from,
        date_to=date_to,
    )

def handle_list_categories(
    db: Session,
    account_id: int | None,
    category: str | None,
    year_transaction: int | None,
    month_transaction: int | None,
) -> list:
    return repo.list_expenses_by_categorie(db,account_id=account_id, category=category, year_transaction=year_transaction, month_transaction=month_transaction)


def handle_list_credit_installments(
    db: Session,
    skip: int,
    limit: int,
    transaction_id: int | None = None,
    account_id: int | None = None,
    account_name: str | None = None,
    description: str | None = None,
    category: str | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
) -> list:
    return repo.list_credit_installments(
        db,
        skip=skip,
        limit=limit,
        transaction_id=transaction_id,
        account_id=account_id,
        account_name=account_name,
        description=description,
        category=category,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
    )

def handle_list_credit_by_account(
    db: Session,
    skip: int,
    limit: int,
    account_id: int | None = None,
    account_name:str | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    year: int | None = None,
    month: int | None = None
) -> list:
    return repo.list_credit_by_account(
        db,
        skip=skip,
        limit=limit,
        account_name=account_name,
        year=year,
        month=month,
        account_id=account_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
    )

def handle_list_credit_by_due_date(
    db: Session,
    skip: int,
    limit: int,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    year: int | None = None,
    month: int | None = None
) -> list:
    return repo.list_credit_by_due_date(
        db,
        skip=skip,
        limit=limit,
        year=year,
        month=month,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
    )


def handle_create(db: Session, payload: TransactionCreate):
    _ensure_account_exists(db, payload.account_id)
    obj = repo.create(db, payload.model_dump())
    return handle_get(db, obj.transaction_id)


_UPDATABLE_FIELDS = {"account_id", "transaction_date", "value", "description", "category", "tracking"}


def _merge_update_data(obj: transaction, data: dict) -> dict:
    return {field: data.get(field, getattr(obj, field)) for field in _UPDATABLE_FIELDS}


def handle_update(
    db: Session, transaction_id: int, payload: TransactionUpdate
):
    obj = handle_get_entity(db, transaction_id)
    data = payload.model_dump(exclude_unset=True)
    invalid_fields = set(data.keys()) - _UPDATABLE_FIELDS
    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid fields: {', '.join(sorted(invalid_fields))}",
        )

    data = _merge_update_data(obj, payload.model_dump(exclude_unset=True))

    if data["account_id"] != obj.account_id:
        _ensure_account_exists(db, data["account_id"])
    repo.update(db, obj, data)
    return handle_get(db, transaction_id)


def handle_delete(db: Session, transaction_id: int) -> None:
    repo.delete(db, handle_get_entity(db, transaction_id))


_REQUIRED_COLUMNS = {"transaction_date", "value", "description"}
_OPTIONAL_COLUMNS = {"accountid_id", "category", "tracking"}

def handle_bulk_upload(db: Session, file_bytes: bytes, filename: str) -> TransactionUploadResult:
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        engine = "openpyxl" if filename.endswith(".xlsx") else "xlrd"
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine=engine)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read file: {exc}")

        df.columns = df.columns.str.strip().str.lower()

        missing = _REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Missing required columns: {', '.join(sorted(missing))}",
            )

        df = df.astype(object).where(df.notna(), None)

        return handle_upload_rows(db, df)

    if filename.endswith(".ofx"):
        return handle_upload_ofx(db, file_bytes)


def handle_upload_ofx(db: Session, file_bytes: bytes) -> TransactionUploadResult:
    try:
        ofx = OfxParser.parse(io.BytesIO(file_bytes))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read OFX file: {exc}")

    try:
        raw_transactions = ofx.account.statement.transactions
    except AttributeError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="OFX file has no transaction data")

    rows = [
        {
            "transaction_date": txn.date.date() if hasattr(txn.date, "date") else txn.date,
            "value": txn.amount,
            "description": txn.memo or txn.payee or "",
        }
        for txn in raw_transactions
    ]
    df = pd.DataFrame(rows)
    return handle_upload_rows(db, df)


def handle_upload_rows(db: Session, df: pd.DataFrame) -> TransactionUploadResult:
    valid_rows: list[dict] = []
    errors: list[UploadRowError] = []

    for idx, row in df.iterrows():
        row_num = int(idx)
        raw_date = row["transaction_date"]
        raw_value = row["value"]
        raw_desc = row["description"]
        raw_category = row.get("category", None)
        raw_account_id = row.get("account_id", 0)
        row_has_error = False

        parsed_category = None if pd.isna(raw_category) else handle_normalize_text(str(raw_category))[:100]

        
        def  _error_row_(message):
            errors.append(UploadRowError(errors={
                "message": message,
                "row": row_num,
                "transaction_date": str(raw_date),
                "value": str(raw_value),
                "description": raw_desc,
                "category": raw_category,
                "account_id": str(raw_account_id)
            }))

        try:
            if raw_account_id: 
                if not bank_accounts_repo.list_all(db, skip=0, limit=1, account_id=int(raw_account_id)):
                    raise ValueError(f"Bank account {raw_account_id} not found")
            parsed_account_id = int(raw_account_id) if raw_account_id else raw_account_id
        except (ValueError, InvalidOperation):
            _error_row_(f"Bank account {raw_account_id} not found")
            row_has_error = True

        try:
            if pd.isna(raw_date):
                raise ValueError("transaction_date is required")
            if isinstance(raw_date, str):
                parsed_date = date.fromisoformat(raw_date.strip())
            else:
                parsed_date = pd.Timestamp(raw_date).date()
        except (ValueError, InvalidOperation):
            _error_row_("transaction date not accepted")
            row_has_error = True

        try:
            if pd.isna(raw_value):
                raise ValueError("value is required")
            parsed_value = Decimal(str(raw_value)).quantize(Decimal("0.0001"))
        except (ValueError, InvalidOperation):
            _error_row_("value not accepted")
            row_has_error = True

        try:
            if pd.isna(raw_desc) or str(raw_desc).strip() == "":
                raise ValueError("description is required")
            parsed_desc = handle_normalize_text(str(raw_desc))[:100]
        except (ValueError, InvalidOperation):
            _error_row_("description not accepted")
            row_has_error = True

        if not row_has_error:
            valid_rows.append({
                "transaction_date": parsed_date,
                "value": parsed_value,
                "description": parsed_desc,
                "account_id": parsed_account_id,
                "category": parsed_category
            })

    if valid_rows:
        repo.bulk_create(db, valid_rows)

    return TransactionUploadResult(created=len(valid_rows), errors=errors)
