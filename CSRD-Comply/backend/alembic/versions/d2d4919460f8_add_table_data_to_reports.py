"""add_table_data_to_reports

Revision ID: d2d4919460f8
Revises: d2d4919460f7
Create Date: 2026-06-11 03:32:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd2d4919460f8'
down_revision: Union[str, None] = 'd2d4919460f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('table_data', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'table_data')