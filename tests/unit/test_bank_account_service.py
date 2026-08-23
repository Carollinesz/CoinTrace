import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services import bank_accounts as service
from app.schemas.schemas import BankAccountCreate, BankAccountUpdate


def _mock_db():
    return MagicMock()


def _make_account(account_id=1, account_name="Conta", account_type="checking", bank_id=1):
    acc = MagicMock()
    acc.account_id = account_id
    acc.account_name = account_name
    acc.account_type = account_type
    acc.bank_id = bank_id
    return acc


# ── handle_get ────────────────────────────────────────────────────────────────

def test_get_not_found_raises_404():
    with patch("app.repositories.bank_accounts.list_all", return_value=[]):
        with pytest.raises(HTTPException) as exc:
            service.handle_get(_mock_db(), 99)
    assert exc.value.status_code == 404


def test_get_returns_account():
    acc = _make_account()
    with patch("app.repositories.bank_accounts.list_all", return_value=[acc]):
        result = service.handle_get(_mock_db(), 1)
    assert result is acc


def test_get_filters_by_account_id():
    db = _mock_db()
    acc = _make_account(account_id=7)
    with patch("app.repositories.bank_accounts.list_all", return_value=[acc]) as mock_list:
        service.handle_get(db, 7)
    assert mock_list.call_args.kwargs["account_id"] == 7


# ── handle_create ─────────────────────────────────────────────────────────────

def test_create_duplicate_name_raises_409():
    existing = _make_account(account_name="Duplicada")
    payload = BankAccountCreate(bank_id=1, account_name="Duplicada", account_type="checking")
    with patch("app.repositories.bank_accounts.list_all", return_value=[existing]):
        with pytest.raises(HTTPException) as exc:
            service.handle_create(_mock_db(), payload)
    assert exc.value.status_code == 409


def test_create_success():
    new = _make_account(account_name="Nova")
    payload = BankAccountCreate(bank_id=1, account_name="Nova", account_type="checking")
    with patch("app.repositories.bank_accounts.list_all", return_value=[]), \
         patch("app.repositories.bank_accounts.create", return_value=new):
        result = service.handle_create(_mock_db(), payload)
    assert result is new


def test_create_partial_name_match_is_not_a_conflict():
    # the name filter matches partially (ILIKE), so only an exact hit is a conflict
    other = _make_account(account_name="Nova Poupanca")
    new = _make_account(account_name="Nova")
    payload = BankAccountCreate(bank_id=1, account_name="Nova", account_type="checking")
    with patch("app.repositories.bank_accounts.list_all", return_value=[other]),          patch("app.repositories.bank_accounts.create", return_value=new):
        result = service.handle_create(_mock_db(), payload)
    assert result is new


# ── handle_update ─────────────────────────────────────────────────────────────

def test_update_name_conflict_raises_409():
    existing = _make_account(account_id=1, account_name="Original")
    other = _make_account(account_id=2, account_name="Ocupada")
    payload = BankAccountUpdate(account_name="Ocupada")
    with patch("app.services.bank_accounts.handle_get", return_value=existing), \
         patch("app.repositories.bank_accounts.list_all", return_value=[other]):
        with pytest.raises(HTTPException) as exc:
            service.handle_update(_mock_db(), 1, payload)
    assert exc.value.status_code == 409


def test_update_same_name_no_conflict():
    acc = _make_account(account_id=1, account_name="Mesma")
    payload = BankAccountUpdate(account_name="Mesma")
    with patch("app.services.bank_accounts.handle_get", return_value=acc), \
         patch("app.repositories.bank_accounts.update", return_value=acc) as mock_update:
        service.handle_update(_mock_db(), 1, payload)
    mock_update.assert_called_once()


# ── handle_delete ─────────────────────────────────────────────────────────────

def test_delete_calls_repo():
    db = _mock_db()
    acc = _make_account()
    with patch("app.services.bank_accounts.handle_get", return_value=acc), \
         patch("app.repositories.bank_accounts.delete") as mock_delete:
        service.handle_delete(db, 1)
    mock_delete.assert_called_once_with(db, acc)


def test_delete_not_found_raises_404():
    with patch("app.services.bank_accounts.handle_get",
               side_effect=HTTPException(status_code=404, detail="not found")):
        with pytest.raises(HTTPException) as exc:
            service.handle_delete(_mock_db(), 99)
    assert exc.value.status_code == 404
