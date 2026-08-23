import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services import fixed_expenses as service
from app.schemas.schemas import FixedExpenseCreate, FixedExpenseUpdate


def _mock_db():
    return MagicMock()


def _make_expense(expense_id=1, name="Netflix", due_day=5, account_id=None, is_active=True):
    e = MagicMock()
    e.expense_id = expense_id
    e.name = name
    e.value = Decimal("55.90")
    e.due_day = due_day
    e.is_active = is_active
    e.account_id = account_id
    e.category = "Outros"
    return e


# ── handle_get ────────────────────────────────────────────────────────────────

def test_get_not_found_raises_404():
    with patch("app.repositories.fixed_expenses.list_all", return_value=[]):
        with pytest.raises(HTTPException) as exc:
            service.handle_get(_mock_db(), 99)
    assert exc.value.status_code == 404


def test_get_returns_expense():
    exp = _make_expense()
    with patch("app.repositories.fixed_expenses.list_all", return_value=[exp]):
        assert service.handle_get(_mock_db(), 1) is exp


# ── handle_create ─────────────────────────────────────────────────────────────

def test_create_with_nonexistent_account_raises_404():
    payload = FixedExpenseCreate(name="Netflix", value=Decimal("55.90"), due_day=5, account_id=999)
    with patch("app.repositories.bank_accounts.list_all", return_value=[]):
        with pytest.raises(HTTPException) as exc:
            service.handle_create(_mock_db(), payload)
    assert exc.value.status_code == 404


def test_create_without_account_skips_account_check():
    exp = _make_expense()
    payload = FixedExpenseCreate(name="Netflix", value=Decimal("55.90"), due_day=5)
    with patch("app.repositories.bank_accounts.list_all") as mock_check, \
         patch("app.repositories.fixed_expenses.create", return_value=exp):
        result = service.handle_create(_mock_db(), payload)
    mock_check.assert_not_called()
    assert result is exp


def test_create_success_with_valid_account():
    exp = _make_expense()
    payload = FixedExpenseCreate(name="Netflix", value=Decimal("55.90"), due_day=5, account_id=1)
    with patch("app.repositories.bank_accounts.list_all", return_value=[MagicMock()]), \
         patch("app.repositories.fixed_expenses.create", return_value=exp):
        assert service.handle_create(_mock_db(), payload) is exp


# ── handle_update ─────────────────────────────────────────────────────────────

def test_update_to_nonexistent_account_raises_404():
    exp = _make_expense()
    payload = FixedExpenseUpdate(account_id=999)
    with patch("app.services.fixed_expenses.handle_get", return_value=exp), \
         patch("app.repositories.bank_accounts.list_all", return_value=[]):
        with pytest.raises(HTTPException) as exc:
            service.handle_update(_mock_db(), 1, payload)
    assert exc.value.status_code == 404


def test_update_null_account_skips_account_check():
    exp = _make_expense(account_id=1)
    payload = FixedExpenseUpdate(account_id=None)
    with patch("app.services.fixed_expenses.handle_get", return_value=exp), \
         patch("app.repositories.bank_accounts.list_all") as mock_check, \
         patch("app.repositories.fixed_expenses.update", return_value=exp):
        service.handle_update(_mock_db(), 1, payload)
    mock_check.assert_not_called()


def test_update_success():
    exp = _make_expense()
    updated = _make_expense(name="Netflix Premium", is_active=False)
    payload = FixedExpenseUpdate(name="Netflix Premium", is_active=False)
    with patch("app.services.fixed_expenses.handle_get", return_value=exp), \
         patch("app.repositories.fixed_expenses.update", return_value=updated):
        result = service.handle_update(_mock_db(), 1, payload)
    assert result.name == "Netflix Premium"
    assert result.is_active is False


# ── handle_delete ─────────────────────────────────────────────────────────────

def test_delete_calls_repo():
    exp = _make_expense()
    with patch("app.services.fixed_expenses.handle_get", return_value=exp), \
         patch("app.repositories.fixed_expenses.delete") as mock_del:
        service.handle_delete(_mock_db(), 1)
    mock_del.assert_called_once()


def test_delete_not_found_raises_404():
    with patch("app.services.fixed_expenses.handle_get",
               side_effect=HTTPException(status_code=404, detail="not found")):
        with pytest.raises(HTTPException) as exc:
            service.handle_delete(_mock_db(), 99)
    assert exc.value.status_code == 404
