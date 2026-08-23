from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import banks
from app.repositories import banks as repo
from app.schemas.schemas import BanksCreate, BanksUpdate

_MAX_LOOKUP = 500  # matches the highest `limit` the endpoints accept


def _find_by_name(db: Session, bank_name: str) -> banks | None:
    matches = repo.list_all(db, skip=0, limit=_MAX_LOOKUP, bank_name=bank_name)
    return next((obj for obj in matches if obj.bank_name == bank_name), None)


def handle_get(db: Session, bank_id: int) -> banks:
    matches = repo.list_all(db, skip=0, limit=1, bank_id=bank_id)
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank {bank_id} not found",
        )
    return matches[0]


def handle_list(
    db: Session,
    skip: int,
    limit: int,
    bank_id: int | None = None,
    bank_name: str | None = None,
) -> list[banks]:
    return repo.list_all(db, skip=skip, limit=limit, bank_id=bank_id, bank_name=bank_name)


def handle_create(db: Session, payload: BanksCreate) -> banks:
    if _find_by_name(db, payload.bank_name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bank '{payload.bank_name}' already exists",
        )
    return repo.create(db, payload.model_dump())


def handle_update(db: Session, bank_id: int, payload: BanksUpdate) -> banks:
    obj = handle_get(db, bank_id)
    data = payload.model_dump(exclude_unset=True)
    if "bank_name" in data and data["bank_name"] != obj.bank_name:
        if _find_by_name(db, data["bank_name"]) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bank '{data['bank_name']}' already exists",
            )
    return repo.update(db, obj, data)


def handle_delete(db: Session, bank_id: int) -> None:
    obj = handle_get(db, bank_id)
    repo.delete(db, obj)
