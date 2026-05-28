"""add esrs_datapoint_cache table

Revision ID: 9b5299a43259
Revises: 9b5299a43258
Create Date: 2026-05-25 06:58:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "9b5299a43259"
down_revision: Union[str, None] = "9b5299a43258"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "esrs_datapoint_cache",
        sa.Column("cache_key", sa.String(512), primary_key=True, nullable=False),
        sa.Column("cache_data", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_esrs_datapoint_cache_key", "esrs_datapoint_cache", ["cache_key"])


def downgrade() -> None:
    op.drop_index("ix_esrs_datapoint_cache_key")
    op.drop_table("esrs_datapoint_cache")
