"""add_status_field_to_lp_details

Revision ID: b8dd2c8c0d06
Revises: 905c3493ab07
Create Date: 2025-04-07 18:59:43.479795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8dd2c8c0d06'
down_revision = '905c3493ab07'
branch_labels = None
depends_on = None


def upgrade():
    # Add status column to lp_details table with default value
    op.add_column('lp_details', sa.Column('status', sa.String(20), nullable=True))
    
    # Set default value for existing records
    op.execute("UPDATE lp_details SET status = 'Waiting For KYC' WHERE status IS NULL")
    
    # Make column non-nullable after setting default values
    op.alter_column('lp_details', 'status', nullable=False, server_default=sa.text("'Waiting For KYC'"))


def downgrade():
    # Remove status column from lp_details table
    op.drop_column('lp_details', 'status')
