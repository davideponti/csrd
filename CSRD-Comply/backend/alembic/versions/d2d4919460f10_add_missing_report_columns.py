"""add_missing_report_columns

Revision ID: d2d4919460f10
Revises: d2d4919460f9
Create Date: 2026-06-12 03:25:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd2d4919460f10'
down_revision: Union[str, None] = 'd2d4919460f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to reports table
    op.add_column('reports', sa.Column('review_comments', sa.JSON(), nullable=True))
    op.add_column('reports', sa.Column('gap_analysis_results', sa.JSON(), nullable=True))
    op.add_column('reports', sa.Column('narrative_content', sa.JSON(), nullable=True))
    op.add_column('reports', sa.Column('ixbrl_tags_applied', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('reports', sa.Column('ixbrl_metadata', sa.JSON(), nullable=True))
    op.add_column('reports', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('reports', sa.Column('approved_by', sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'approved_by')
    op.drop_column('reports', 'approved_at')
    op.drop_column('reports', 'ixbrl_metadata')
    op.drop_column('reports', 'ixbrl_tags_applied')
    op.drop_column('reports', 'narrative_content')
    op.drop_column('reports', 'gap_analysis_results')
    op.drop_column('reports', 'review_comments')
