"""add extended_kpis to company_context_settings

Revision ID: d2d4919460f11
Revises: d2d4919460f10
Create Date: 2026-06-12 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2d4919460f11'
down_revision: Union[str, None] = 'd2d4919460f10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'company_context_settings',
        sa.Column('extended_kpis', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('company_context_settings', 'extended_kpis')
