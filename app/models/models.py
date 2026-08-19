from decimal import Decimal
from datetime import datetime, date
from app.core.config import settings
from app.core.database import engine_migrations

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, TIMESTAMP, func, event, text
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

    transaction_id:   Mapped[int]            = mapped_column(init=False, primary_key=True, autoincrement=True)
    transaction_date: Mapped[date]           = mapped_column(Date, nullable=False)
    value:            Mapped[Decimal]        = mapped_column(Numeric(10, 4), nullable=False)
    description:      Mapped[str]            = mapped_column(String(100), nullable=False)
    account_id:       Mapped[int]            = mapped_column(nullable=False, default=0, server_default="0")
    type:             Mapped[str]            = mapped_column(String(50), nullable=False, default='debit')
    details:          Mapped[dict | None]     = mapped_column(JSONB, nullable=True, default=None)
    category:         Mapped[str]            = mapped_column(String(100), nullable=True, default='Outros')
    tracking:         Mapped[bool]           = mapped_column(nullable=False, default=True, server_default='true')
    created_at:       Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, init=False)

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


from app.constants.avaliable_banks import brazilian_banks

@event.listens_for(banks.__table__, 'after_create')
def insert_default_bank(target, connection, **kw):
    for bank in brazilian_banks:
        connection.execute(
            target.insert().values(bank_name=bank)
        )
    connection.execute(
        text("SELECT setval(pg_get_serial_sequence('avaliable_banks', 'bank_id'), (SELECT MAX(bank_id) FROM avaliable_banks))")
    )

Base.metadata.create_all(engine_migrations)

_VIEWS = [
    """
    CREATE OR REPLACE VIEW credit_installments_view AS
    SELECT
        t.transaction_id,
        t.account_id,
        t.description,
        t.category,
        t.transaction_date,
        t.value                                                      AS total_value,
        (t.details->>'installments')::int                            AS total_installments,
        gs.n                                                         AS installment_number,
        (t.details->>'first_payment')::date
            + make_interval(months => gs.n - 1)                      AS due_date,
        COALESCE((t.details->>'interest')::numeric, 0)               AS interest_rate,
        CASE
            WHEN COALESCE((t.details->>'interest')::numeric, 0) = 0 THEN
                ROUND(t.value / (t.details->>'installments')::int, 4)
            ELSE
                ROUND(
                    t.value
                    * ((t.details->>'interest')::numeric
                       * POWER(1 + (t.details->>'interest')::numeric,
                               (t.details->>'installments')::int))
                    / (POWER(1 + (t.details->>'interest')::numeric,
                             (t.details->>'installments')::int) - 1),
                    4)
        END                                                          AS installment_value
    FROM transactions t
    CROSS JOIN LATERAL generate_series(1, (t.details->>'installments')::int) AS gs(n)
    WHERE t.type = 'credit'
      AND t.details IS NOT NULL
      AND (t.details->>'installments') IS NOT NULL
      AND (t.details->>'first_payment') IS NOT NULL
    """,
    """
    CREATE OR REPLACE VIEW bank_account_balance_view AS
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
    GROUP BY ba.account_id, ba.account_name, ba.account_type, ba.start_value
    """,
]

with engine_migrations.connect() as _conn:
    for _sql in _VIEWS:
        _conn.execute(text(_sql))
    _conn.commit()

if settings.DEMO:
    from app.core.demo_seed import handle_seed_demo_data

    handle_seed_demo_data(engine_migrations)