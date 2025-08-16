"""add_nav_and_mgmt_fee_to_funds

Revision ID: 001_add_nav_and_mgmt_fee_to_funds
Revises: cdfa556e8bc1
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '1361d69e190'
branch_labels = None
depends_on = None


def upgrade():
    # Add mgmt_fee_rate column to fund_details table with default 1% (0.01)
    op.add_column('fund_details', sa.Column('mgmt_fee_rate', sa.DECIMAL(5,4), nullable=False, server_default='0.0100'))
    
    # Add stamp_duty_rate column to fund_details table with default 0.005% (0.00005)
    op.add_column('fund_details', sa.Column('stamp_duty_rate', sa.DECIMAL(8,7), nullable=False, server_default='0.0000500'))
    
    # nav column remains INTEGER with default value 100
    op.alter_column('fund_details', 'nav',
                    existing_type=sa.INTEGER(),
                    nullable=False,
                    server_default='100')


def downgrade():
    # Remove mgmt_fee_rate and stamp_duty_rate columns
    op.drop_column('fund_details', 'mgmt_fee_rate')
    op.drop_column('fund_details', 'stamp_duty_rate')
    
    # nav column remains INTEGER - no change needed in downgrade
    # (it was already INTEGER in the original state)