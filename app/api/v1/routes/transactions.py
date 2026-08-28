from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import CreditInstallmentRead, TransactionCreate, TransactionRead, TransactionUpdate, TransactionUploadResult, TransactionsCategory
from app.services import transactions as service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
def handle_list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    transaction_id: int | None = Query(None),
    description: str | None = Query(None),
    account_id: int | None = Query(None),
    type: str | None = Query(None),
    category: str | None = Query(None),
    tracking: bool | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list(
        db,
        skip=skip,
        limit=limit,
        description=description,
        transaction_id=transaction_id,
        account_id=account_id,
        type=type,
        category=category,
        tracking=tracking,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/credit-installments", response_model=list[CreditInstallmentRead])
def handle_list_credit_installments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    transaction_id: int | None = Query(None),
    account_id: int | None = Query(None),
    description: str | None = Query(None),
    category: str | None = Query(None),
    due_date_from: date | None = Query(None),
    due_date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list_credit_installments(
        db,
        skip=skip,
        limit=limit,
        transaction_id=transaction_id,
        account_id=account_id,
        description=description,
        category=category,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
    )

@router.get("/categories", response_model=list[TransactionsCategory])
def handle_list_categories(
    account_id: int | None = Query(None),
    category: str | None = Query(None),
    year_transaction: int | None = Query(None),
    month_transaction: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return service.handle_list_categories(db, account_id=account_id, category=category, year_transaction=year_transaction, month_transaction=month_transaction)




@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def handle_create_transaction(
    payload: TransactionCreate, db: Session = Depends(get_db)
):
    try:
        return service.handle_create(db, payload)
    except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )


@router.patch("/{transaction_id}", response_model=TransactionRead)
def handle_update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
):
    return service.handle_update(db, transaction_id, payload)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def handle_delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    service.handle_delete(db, transaction_id)


@router.post("/upload", response_model=TransactionUploadResult, status_code=status.HTTP_200_OK)
async def handle_upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""
    if not (filename.endswith(".xlsx") or filename.endswith(".xls") or filename.endswith(".ofx")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .xlsx, .xls, .ofx files are supported",
        )
    contents = await file.read()
    return service.handle_bulk_upload(db, contents, filename)
