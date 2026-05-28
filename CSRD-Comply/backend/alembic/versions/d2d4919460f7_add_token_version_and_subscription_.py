"""add_token_version_and_subscription_columns

Revision ID: d2d4919460f7
Revises: 9b5299a43259
Create Date: 2026-05-25 07:07:44.355439
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd2d4919460f7'
down_revision: Union[str, None] = 'd2d4919460f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add token_version to users table
    op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))
    
    # Add subscription metadata columns
    op.add_column('subscriptions', sa.Column('billing_cycle', sa.String(length=20), nullable=False, server_default='monthly'))
    op.add_column('subscriptions', sa.Column('current_period_start', sa.Date(), nullable=True))
    op.add_column('subscriptions', sa.Column('current_period_end', sa.Date(), nullable=True))
    op.add_column('subscriptions', sa.Column('trial_end', sa.Date(), nullable=True))
    op.add_column('subscriptions', sa.Column('canceled_at', sa.DateTime(), nullable=True))
    op.add_column('subscriptions', sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('users', 'token_version')
    op.drop_column('subscriptions', 'billing_cycle')
    op.drop_column('subscriptions', 'current_period_start')
    op.drop_column('subscriptions', 'current_period_end')
    op.drop_column('subscriptions', 'trial_end')
    op.drop_column('subscriptions', 'canceled_at')
    op.drop_column('subscriptions', 'auto_renew')
