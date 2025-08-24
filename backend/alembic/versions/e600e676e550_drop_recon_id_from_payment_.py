"""drop_recon_id_from_payment_reconciliation

Revision ID: e600e676e550
Revises: c3243d35eb04
Create Date: 2025-08-23 21:43:13.572885

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e600e676e550'
down_revision = 'c3243d35eb04'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the redundant recon_id column from payment_reconciliation table
    op.drop_column('payment_reconciliation', 'recon_id')


def downgrade():
    # Add back the recon_id column if needed to rollback
    op.add_column('payment_reconciliation', 
                  sa.Column('recon_id', sa.BigInteger(), autoincrement=True, nullable=False))
