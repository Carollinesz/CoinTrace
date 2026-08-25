import pytest

from app.schemas.schemas import FixedExpenseCreate, TransactionCreate
from app.utils.text_functions import handle_normalize_text


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  alimentacao   FORA ", "Alimentacao Fora"),
        ("ALIMENTAÇÃO", "Alimentação"),
        ("cartão  de credito", "Cartão De Credito"),
        ("Mercado", "Mercado"),
        ("", ""),
    ],
)
def test_normalize_text(raw, expected):
    assert handle_normalize_text(raw) == expected


@pytest.mark.parametrize("raw", [None, 5])
def test_normalize_text_keeps_non_strings(raw):
    assert handle_normalize_text(raw) is raw


def test_transaction_create_normalizes_description_and_category():
    payload = TransactionCreate(
        transaction_date="2026-08-24",
        value="10.50",
        description="  PAGAMENTO   pix  ",
        category=" mercado ",
    )
    assert payload.description == "Pagamento Pix"
    assert payload.category == "Mercado"


def test_transaction_create_keeps_category_none():
    payload = TransactionCreate(transaction_date="2026-08-24", value="10.50", description="Uber")
    assert payload.category is None


def test_fixed_expense_create_normalizes_category():
    payload = FixedExpenseCreate(name="Netflix", value="39.90", due_day=10, category="  streaming  DIGITAL ")
    assert payload.category == "Streaming Digital"
