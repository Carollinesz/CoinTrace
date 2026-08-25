"""add description indexes

Revision ID: 766fc8d9b55a
Revises: 0a42e6f4598b
Create Date: 2026-08-25 00:09:10.667185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '766fc8d9b55a'
down_revision: Union[str, None] = '0a42e6f4598b'
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


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_transaction_description")
