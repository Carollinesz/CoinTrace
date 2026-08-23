import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services import transactions as service
from app.schemas.schemas import TransactionCreate, TransactionUpdate


def _mock_db():
    return MagicMock()


def _make_txn(transaction_id=1, description="Test", type="debit", account_id=1):
    t = MagicMock()
    t.transaction_id = transaction_id
    t.description = description
    t.type = type
    t.account_id = account_id
    t.transaction_date = date(2024, 1, 15)
    t.value = Decimal("-50.00")
    t.category = "Outros"
    t.tracking = True
    return t


# ── handle_get ────────────────────────────────────────────────────────────────

def test_get_not_found_raises_404():
    with patch("app.repositories.transactions.list_all", return_value=[]):
        with pytest.raises(HTTPException) as exc:
            service.handle_get(_mock_db(), 99)
    assert exc.value.status_code == 404


def test_get_returns_transaction():
    txn = _make_txn()
    with patch("app.repositories.transactions.list_all", return_value=[txn]):
        assert service.handle_get(_mock_db(), 1) is txn


# ── handle_create ─────────────────────────────────────────────────────────────

def test_create_account_not_found_raises_404():
    payload = TransactionCreate(
        account_id=999,
        transaction_date=date(2024, 1, 15),
        value=Decimal("-50.00"),
        description="Test",
    )
    with patch("app.repositories.bank_accounts.list_all", return_value=[]):
        with pytest.raises(HTTPException) as exc:
            service.handle_create(_mock_db(), payload)
    assert exc.value.status_code == 404


def test_create_success():
    txn = _make_txn()
    payload = TransactionCreate(
        account_id=1,
        transaction_date=date(2024, 1, 15),
        value=Decimal("-50.00"),
        description="Test",
    )
    with patch("app.repositories.bank_accounts.list_all", return_value=[MagicMock()]), \
         patch("app.repositories.transactions.create", return_value=txn):
        assert service.handle_create(_mock_db(), payload) is txn


# ── handle_update ─────────────────────────────────────────────────────────────

def test_update_immutable_field_raises_422():
    txn = _make_txn()
    payload = TransactionUpdate(type="credit")  # 'type' is not in _UPDATABLE_FIELDS
    with patch("app.services.transactions.handle_get", return_value=txn):
        with pytest.raises(HTTPException) as exc:
            service.handle_update(_mock_db(), 1, payload)
    assert exc.value.status_code == 422


def test_update_account_change_to_nonexistent_raises_404():
    txn = _make_txn(account_id=1)
    payload = TransactionUpdate(account_id=999)
    with patch("app.services.transactions.handle_get", return_value=txn), \
         patch("app.repositories.bank_accounts.list_all", return_value=[]):
        with pytest.raises(HTTPException) as exc:
            service.handle_update(_mock_db(), 1, payload)
    assert exc.value.status_code == 404


def test_update_success():
    txn = _make_txn()
    updated = _make_txn(description="Padaria")
    payload = TransactionUpdate(description="Padaria")
    with patch("app.services.transactions.handle_get", return_value=txn), \
         patch("app.repositories.transactions.update", return_value=updated):
        result = service.handle_update(_mock_db(), 1, payload)
    assert result.description == "Padaria"


# ── handle_delete ─────────────────────────────────────────────────────────────

def test_delete_calls_repo():
    txn = _make_txn()
    with patch("app.services.transactions.handle_get", return_value=txn), \
         patch("app.repositories.transactions.delete") as mock_del:
        service.handle_delete(_mock_db(), 1)
    mock_del.assert_called_once()


def test_delete_not_found_raises_404():
    with patch("app.services.transactions.handle_get",
               side_effect=HTTPException(status_code=404, detail="not found")):
        with pytest.raises(HTTPException) as exc:
            service.handle_delete(_mock_db(), 99)
    assert exc.value.status_code == 404
