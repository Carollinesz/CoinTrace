from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Optional


from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def handle_quantize_money(value) -> Decimal:
    """Columns and views keep 4 decimals; responses expose cents."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


Money = Annotated[Decimal, Field(max_digits=15, decimal_places=2)]
MoneyOut = Annotated[Decimal, BeforeValidator(handle_quantize_money), Field(max_digits=15, decimal_places=2)]


# ── Bank Account ──────────────────────────────────────────────────────────────

class BankAccountCreate(BaseModel):
    bank_id:        int
    account_name:   str
    account_type:   str
    start_value:    float = 0.0000


class BankAccountUpdate(BaseModel):
    account_name:      str | None = None
    account_type:   str | None = None
    start_value:    float | None = None


class BankAccountRead(BankAccountCreate):
    model_config = ConfigDict(from_attributes=True)

    account_id: int


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    account_id:       int  | None = 0
    transaction_date: date
    value:            Money
    description:      str
    category:         str  | None = None
    type:             str  | None = 'debit'
    details:          Optional[dict] = None
    tracking:         bool = True


class TransactionUpdate(BaseModel):
    account_id:       int | None = None
    transaction_date: date | None = None
    value:            Money | None = None
    description:      str | None = None
    category:         str | None = None
    type:             str | None = None
    details:          Optional[dict] = None
    tracking:         bool | None = None


class TransactionRead(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    created_at:     datetime


# ── Fixed Expense ─────────────────────────────────────────────────────────────

class FixedExpenseCreate(BaseModel):
    name:       str
    value:      Money
    due_day:    int = Field(ge=1, le=31)
    category:   str | None = 'Outros'
    account_id: int | None = None
    is_active:  bool = True


class FixedExpenseUpdate(BaseModel):
    name:       str | None = None
    value:      Money | None = None
    due_day:    int | None = Field(default=None, ge=1, le=31)
    category:   str | None = None
    account_id: int | None = None
    is_active:  bool | None = None


class FixedExpenseRead(FixedExpenseCreate):
    model_config = ConfigDict(from_attributes=True)

    expense_id: int
    created_at: datetime


# ── Bank Account Balance View ─────────────────────────────────────────────────

class BankAccountBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id:      int
    account_name:    str
    account_type:    str
    start_value:     MoneyOut
    total_gains:     MoneyOut
    total_expenses:  MoneyOut
    current_balance: MoneyOut


# ── Credit Installments View ──────────────────────────────────────────────────

class CreditInstallmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id:     int
    account_id:         int | None
    description:        str
    category:           str | None
    transaction_date:   date
    total_value:        MoneyOut
    total_installments: int
    installment_number: int
    due_date:           date
    interest_rate:      Decimal
    installment_value:  MoneyOut


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadRowError(BaseModel):
    errors:   dict 


class TransactionUploadResult(BaseModel):
    created: int
    errors: list[UploadRowError]

# ── Banks ───────────────────────────────────────────────────────────────


class BanksCreate(BaseModel):
    bank_name: str


class BanksUpdate(BaseModel):
    bank_name: str | None = None


class BanksRead(BanksCreate):
    model_config = ConfigDict(from_attributes=True)

    bank_id: int

