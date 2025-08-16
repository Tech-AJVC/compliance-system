"""create_unit_allotments_table

Revision ID: 002_create_unit_allotments_table
Revises: 001_add_nav_and_mgmt_fee_to_funds
Create Date: 2025-01-27 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g7h8i9j0k1l2'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Create unit_allotments table
    op.create_table('unit_allotments',
        sa.Column('allotment_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('drawdown_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lp_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fund_id', sa.Integer(), nullable=False),
        sa.Column('clid', sa.String(length=60), nullable=True),
        sa.Column('depository', sa.String(length=60), nullable=True),
        sa.Column('dpid', sa.String(length=20), nullable=True),
        sa.Column('first_holder_name', sa.String(length=255), nullable=False),
        sa.Column('first_holder_pan', sa.String(length=20), nullable=True),
        sa.Column('second_holder_name', sa.String(length=255), nullable=True),
        sa.Column('second_holder_pan', sa.String(length=20), nullable=True),
        sa.Column('third_holder_name', sa.String(length=255), nullable=True),
        sa.Column('third_holder_pan', sa.String(length=20), nullable=True),
        sa.Column('mgmt_fees', sa.DECIMAL(18,2), nullable=False),
        sa.Column('committed_amt', sa.DECIMAL(18,2), nullable=False),
        sa.Column('amt_accepted', sa.DECIMAL(18,2), nullable=False),
        sa.Column('drawdown_amount', sa.DECIMAL(18,2), nullable=False),
        sa.Column('drawdown_date', sa.Date(), nullable=False),
        sa.Column('drawdown_quarter', sa.String(length=20), nullable=False),
        sa.Column('nav_value', sa.DECIMAL(10,2), nullable=False),
        sa.Column('allotted_units', sa.Integer(), nullable=False),
        sa.Column('stamp_duty', sa.DECIMAL(10,2), nullable=False),
        sa.Column('bank_account_no', sa.String(length=50), nullable=True),
        sa.Column('bank_account_name', sa.String(length=255), nullable=True),
        sa.Column('bank_ifsc', sa.String(length=15), nullable=True),
        sa.Column('micr_code', sa.String(length=50), nullable=True),
        sa.Column('date_of_allotment', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False, server_default='Generated'),
        sa.Column('excel_file_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['drawdown_id'], ['lp_drawdowns.drawdown_id'], ),
        sa.ForeignKeyConstraint(['lp_id'], ['lp_details.lp_id'], ),
        sa.ForeignKeyConstraint(['fund_id'], ['fund_details.fund_id'], ),
        
        # Primary key
        sa.PrimaryKeyConstraint('allotment_id')
    )
    
    # Create indexes for performance
    op.create_index('idx_unit_allotments_fund_id', 'unit_allotments', ['fund_id'])
    op.create_index('idx_unit_allotments_lp_id', 'unit_allotments', ['lp_id'])
    op.create_index('idx_unit_allotments_drawdown_quarter', 'unit_allotments', ['drawdown_quarter'])
    op.create_index('idx_unit_allotments_status', 'unit_allotments', ['status'])
    op.create_index('idx_unit_allotments_created_at', 'unit_allotments', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_unit_allotments_created_at')
    op.drop_index('idx_unit_allotments_status')
    op.drop_index('idx_unit_allotments_drawdown_quarter')
    op.drop_index('idx_unit_allotments_lp_id')
    op.drop_index('idx_unit_allotments_fund_id')
    
    # Drop table
    op.drop_table('unit_allotments')