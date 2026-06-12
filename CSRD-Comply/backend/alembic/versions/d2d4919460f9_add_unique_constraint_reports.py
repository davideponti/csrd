"""add_unique_constraint_reports

Revision ID: d2d4919460f9
Revises: d2d4919460f8
Create Date: 2026-06-12 02:15:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd2d4919460f9'
down_revision: Union[str, None] = 'd2d4919460f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint on company_id + title + reporting_year
    # First clean up any existing duplicates (keep the most recent one by updated_at)
    op.execute("""
        DELETE FROM reports a USING (
            SELECT MIN(id) as id, company_id, title, reporting_year
            FROM reports
            GROUP BY company_id, title, reporting_year
            HAVING COUNT(*) > 1
        ) b
        WHERE a.company_id = b.company_id
          AND a.title = b.title
          AND a.reporting_year = b.reporting_year
          AND a.id != b.id
    """)
    op.create_unique_constraint(
        'uq_report_company_title_year',
        'reports',
        ['company_id', 'title', 'reporting_year']
    )


def downgrade() -> None:
    op.drop_constraint('uq_report_company_title_year', 'reports', type_='unique')
