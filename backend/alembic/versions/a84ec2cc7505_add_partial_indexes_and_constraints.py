"""add partial indexes and constraints

Revision ID: a84ec2cc7505
Revises: 46d1bd4cdeca
Create Date: 2026-08-08 03:07:40.827632

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a84ec2cc7505'
down_revision: Union[str, None] = '46d1bd4cdeca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Una sola dirección principal por cliente (índice único parcial, ver docs/database.md)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_customer_single_principal_address
        ON customer_addresses (customer_id)
        WHERE es_principal = true
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_customer_single_principal_address")
