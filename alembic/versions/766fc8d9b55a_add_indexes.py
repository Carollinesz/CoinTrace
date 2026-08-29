"""add description indexes

Revision ID: 766fc8d9b55a
Revises: e1e679c84ec1
Create Date: 2026-08-25 00:09:10.667185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '766fc8d9b55a'
down_revision: Union[str, None] = 'e1e679c84ec1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Must stay byte-identical to the expression built in app/repositories/transactions.py,
# otherwise the planner cannot recognise the index and falls back to a sequential scan.
DESCRIPTION_TSVECTOR = (
    "to_tsvector('portuguese', description) || to_tsvector('english', description)"
)


def upgrade() -> None:
    op.execute(
        f"""
        CREATE INDEX idx_transaction_description
        ON transactions
        USING gin (({DESCRIPTION_TSVECTOR}))
        """
    )
    op.execute("CREATE INDEX idx_transaction_date ON transactions (transaction_date)")
    op.execute("CREATE INDEX idx_transaction_account_categories ON transactions (account_id, category)")
    op.execute("CREATE INDEX idx_transaction_date_categories ON transactions (category, year_transaction, month_transaction)")
    op.execute("CREATE INDEX idx_transaction_datetime_categories ON transactions (category, transaction_date)")
    
def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_transaction_date")
    op.execute("DROP INDEX IF EXISTS idx_transaction_description")
    op.execute("DROP INDEX IF EXISTS idx_transaction_account_categories")
    op.execute("DROP INDEX IF EXISTS idx_transaction_date_categories")
    op.execute("DROP INDEX IF EXISTS idx_transaction_datetime_categories")
