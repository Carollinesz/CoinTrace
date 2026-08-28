from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, registry, MappedAsDataclass
from sqlalchemy.dialects.postgresql import JSONB



class Base(DeclarativeBase, MappedAsDataclass):
    pass

class bank_account(Base):
    __tablename__ = "bank_accounts"

    account_id:       Mapped[int]           = mapped_column(init=False, primary_key=True, autoincrement=True)
    bank_id:          Mapped[int]           = mapped_column(nullable=False)
    account_name:     Mapped[str]           = mapped_column(String(100), nullable=False, unique=True)  
    account_type:     Mapped[str]           = mapped_column(String(100), nullable=False)
    start_value:      Mapped[Decimal]       = mapped_column(Numeric(10, 4), nullable=True, default=0.0)
    created_at:       Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, init=False)

    __table_args__ = (
        CheckConstraint("-999000000000 < start_value AND start_value < 999000000000", name="check_start_value_limit"),
    )

class transaction(Base):
    __tablename__ = "transactions"

    transaction_id:         Mapped[int]            = mapped_column(init=False, primary_key=True, autoincrement=True)
    transaction_date:       Mapped[date]           = mapped_column(Date, nullable=False)
    value:                  Mapped[Decimal]        = mapped_column(Numeric(10, 4), nullable=False)
    description:            Mapped[str]            = mapped_column(String(100), nullable=False)
    month_transaction:      Mapped[int]            
    year_transaction:       Mapped[int]            
    day_transaction:        Mapped[int] 
    account_id:             Mapped[int]            = mapped_column(nullable=False, default=0, server_default="0")           
    type:                   Mapped[str]            = mapped_column(String(50), nullable=False, default='debit')
    details:                Mapped[dict | None]    = mapped_column(JSONB, nullable=True, default=None)
    category:               Mapped[str]            = mapped_column(String(100), nullable=True, default='Outros')
    tracking:               Mapped[bool]           = mapped_column(nullable=False, default=True, server_default='true')
    created_at:             Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, init=False)

    def __post_init__(self):
        if self.type == "credit":
            if not self.details:
                raise ValueError("Credit transactions require the 'details' dictionary.")

            if "installments" not in self.details:
                self.details['installments'] = 1

            if "interest" not in self.details:
                self.details['interest'] = 0.0000

            installments = self.details["installments"] 
            if not (1 <= installments <= 99):
                raise ValueError("The number of installments must be between 1 and 99")
                
            if "first_payment" not in self.details:
                raise ValueError("Transações de crédito precisam de 'first_payment'.")

            fp = self.details["first_payment"]
            if isinstance(fp, str):
                try:
                    date.fromisoformat(fp)
                except ValueError:
                    raise ValueError("first_payment string must be in YYYY-MM-DD format")
            elif not isinstance(fp, date):
                raise ValueError("first_payment must be a date type or a valid ISO date string")

class banks(Base):
    __tablename__ = "avaliable_banks"

    bank_id:       Mapped[int]           = mapped_column(init=False, primary_key=True, autoincrement=True)
    bank_name:     Mapped[str]           = mapped_column(String(100), nullable=False)
    created_at:    Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, init=False)


class fixed_expense(Base):
    __tablename__ = "fixed_expenses"

    expense_id:   Mapped[int]           = mapped_column(init=False, primary_key=True, autoincrement=True)
    name:         Mapped[str]           = mapped_column(String(100), nullable=False)
    value:        Mapped[Decimal]       = mapped_column(Numeric(10, 4), nullable=False)
    due_day:      Mapped[int]           = mapped_column(nullable=False)
    category:     Mapped[str]           = mapped_column(String(100), nullable=True, default='Outros')
    account_id:   Mapped[int]           = mapped_column(nullable=True, default=None)
    is_active:    Mapped[bool]          = mapped_column(nullable=False, default=True)
    created_at:   Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, init=False)

    __table_args__ = (
        CheckConstraint("due_day >= 1 AND due_day <= 31", name="check_due_day_range"),
    )
