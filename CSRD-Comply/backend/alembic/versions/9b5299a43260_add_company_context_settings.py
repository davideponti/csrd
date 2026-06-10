"""Add company_context_settings table

Revision ID: 9b5299a43260
Revises: d2d4919460f7
Create Date: 2026-10-06 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9b5299a43260'
down_revision: Union[str, None] = 'd2d4919460f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'company_context_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('now()')),

        # ── COMPANY PROFILE ─────────────────────────────────────
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('country', sa.String(255), nullable=True),
        sa.Column('sector', sa.String(255), nullable=True),
        sa.Column('reporting_year', sa.Integer(), nullable=True),
        sa.Column('employee_count_total', sa.Integer(), nullable=True),
        sa.Column('employee_count_permanent', sa.Integer(), nullable=True),
        sa.Column('employee_count_temporary', sa.Integer(), nullable=True),
        sa.Column('employee_count_male', sa.Integer(), nullable=True),
        sa.Column('employee_count_female', sa.Integer(), nullable=True),
        sa.Column('employee_count_other', sa.Integer(), nullable=True),
        sa.Column('employee_count_by_geography', postgresql.JSON(), nullable=True),
        sa.Column('annual_revenue_eur', sa.Float(), nullable=True),
        sa.Column('operational_sites_count', sa.Integer(), nullable=True),

        # ── GHG EMISSIONS ───────────────────────────────────────
        sa.Column('scope1_emissions', sa.Float(), nullable=True),
        sa.Column('scope2_location_based', sa.Float(), nullable=True),
        sa.Column('scope2_market_based', sa.Float(), nullable=True),
        sa.Column('scope3_total', sa.Float(), nullable=True),
        sa.Column('scope3_material_categories', postgresql.JSON(), nullable=True),
        sa.Column('emissions_baseline_year', sa.Integer(), nullable=True),
        sa.Column('emissions_methodology', sa.String(255), nullable=True),

        # ── SUPPLY CHAIN ────────────────────────────────────────
        sa.Column('tier1_suppliers_count', sa.Integer(), nullable=True),
        sa.Column('tier2_suppliers_count', sa.Integer(), nullable=True),
        sa.Column('value_chain_countries', postgresql.JSON(), nullable=True),
        sa.Column('high_risk_countries', postgresql.JSON(), nullable=True),
        sa.Column('suppliers_code_of_conduct_pct', sa.Float(), nullable=True),
        sa.Column('supplier_audits_last_year', sa.Integer(), nullable=True),

        # ── WORKFORCE KPIs ──────────────────────────────────────
        sa.Column('ltifr', sa.Float(), nullable=True),
        sa.Column('fatal_accidents', sa.Integer(), nullable=True),
        sa.Column('voluntary_turnover_pct', sa.Float(), nullable=True),
        sa.Column('avg_training_hours_per_year', sa.Float(), nullable=True),
        sa.Column('women_in_management_pct', sa.Float(), nullable=True),
        sa.Column('gender_pay_gap_pct', sa.Float(), nullable=True),
        sa.Column('union_coverage_pct', sa.Float(), nullable=True),
        sa.Column('employee_engagement_score', sa.Float(), nullable=True),

        # ── PAYMENT PRACTICES ───────────────────────────────────
        sa.Column('standard_payment_terms_days', sa.Integer(), nullable=True),
        sa.Column('avg_actual_payment_time_days', sa.Float(), nullable=True),
        sa.Column('invoices_paid_within_terms_pct', sa.Float(), nullable=True),
        sa.Column('invoices_paid_late_pct', sa.Float(), nullable=True),

        # ── GOVERNANCE ──────────────────────────────────────────
        sa.Column('anti_corruption_training_pct', sa.Float(), nullable=True),
        sa.Column('corruption_incidents_last_year', sa.Integer(), nullable=True),
        sa.Column('whistleblowing_reports_received', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], ),
        sa.UniqueConstraint('company_id'),
    )
    op.create_index(
        'ix_company_context_settings_company_id',
        'company_context_settings',
        ['company_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ix_company_context_settings_company_id',
                  table_name='company_context_settings')
    op.drop_table('company_context_settings')
