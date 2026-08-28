"""drop credit installments view

Revision ID: 9f2c5b71a4d3
Revises: 766fc8d9b55a
Create Date: 2026-08-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9f2c5b71a4d3'
down_revision: Union[str, None] = '766fc8d9b55a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# The installment breakdown now lives in app/repositories/transactions.py and is served by
# GET /transactions/credit-installments, so the view has no readers left.
CREDIT_INSTALLMENTS_VIEW = """
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
"""


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS credit_installments_view")


def downgrade() -> None:
    op.execute(CREDIT_INSTALLMENTS_VIEW)
