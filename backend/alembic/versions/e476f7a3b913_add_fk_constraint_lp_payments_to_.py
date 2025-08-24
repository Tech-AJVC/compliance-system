"""add_fk_constraint_lp_payments_to_payment_reconciliation

Revision ID: e476f7a3b913
Revises: e600e676e550
Create Date: 2025-08-23 23:13:07.023583

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e476f7a3b913'
down_revision = 'e600e676e550'
branch_labels = None
depends_on = None


def upgrade():
    # Add foreign key constraint from lp_payments.payment_id to payment_reconciliation.payment_id
    op.create_foreign_key(
        'fk_lp_payments_payment_reconciliation',
        'lp_payments',
        'payment_reconciliation',
        ['payment_id'],
        ['payment_id']
    )


def downgrade():
    # Drop the foreign key constraint
    op.drop_constraint('fk_lp_payments_payment_reconciliation', 'lp_payments', type_='foreignkey')
