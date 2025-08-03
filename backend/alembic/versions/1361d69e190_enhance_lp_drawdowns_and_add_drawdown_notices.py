"""enhance_lp_drawdowns_and_add_drawdown_notices

Revision ID: 1361d69e190
Revises: ee02e213762d
Create Date: 2025-08-01 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '1361d69e190'
down_revision = '3147afcb16b5'
branch_labels = None
depends_on = None


def upgrade():
    # Create drawdown_notices table
    op.create_table('drawdown_notices',
        sa.Column('notice_id', UUID(as_uuid=True), nullable=False),
        sa.Column('drawdown_id', UUID(as_uuid=True), nullable=False),
        sa.Column('lp_id', UUID(as_uuid=True), nullable=False),
        sa.Column('notice_date', sa.Date(), nullable=False),
        sa.Column('amount_due', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('pdf_file_path', sa.String(length=500), nullable=True),
        sa.Column('document_id', UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_channel', sa.String(length=30), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ),
        sa.ForeignKeyConstraint(['drawdown_id'], ['lp_drawdowns.drawdown_id'], ),
        sa.ForeignKeyConstraint(['lp_id'], ['lp_details.lp_id'], ),
        sa.PrimaryKeyConstraint('notice_id')
    )

    # Enhance lp_drawdowns table - drop old columns first, then add new ones
    # Since this is a major restructure, we'll handle it carefully
    
    # Add new columns to lp_drawdowns
    op.add_column('lp_drawdowns', sa.Column('notice_date', sa.Date(), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('drawdown_due_date', sa.Date(), nullable=True)) 
    op.add_column('lp_drawdowns', sa.Column('drawdown_quarter', sa.String(length=20), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('committed_amt', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('drawdown_amount', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('amount_called_up', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('remaining_commitment', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('forecast_next_quarter', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('forecast_next_quarter_period', sa.String(length=20), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('status', sa.String(length=50), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('amt_accepted', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('allotted_units', sa.Integer(), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('nav_value', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('date_of_allotment', sa.Date(), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('mgmt_fees', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('lp_drawdowns', sa.Column('stamp_duty', sa.Numeric(precision=10, scale=2), nullable=True))
    
    # Alter existing columns to match new schema
    op.alter_column('lp_drawdowns', 'fund_id', 
                    existing_type=sa.Integer(),
                    nullable=False)
    
    # Drop old columns instead of renaming
    op.drop_column('lp_drawdowns', 'drawdown_date')
    op.drop_column('lp_drawdowns', 'amount')
    op.drop_column('lp_drawdowns', 'payment_due_date')
    op.drop_column('lp_drawdowns', 'payment_status')
    
    # Set default values for new required columns
    op.execute("UPDATE lp_drawdowns SET status = 'Sent' WHERE status IS NULL")
    op.execute("UPDATE lp_drawdowns SET drawdown_quarter = 'Q1''25' WHERE drawdown_quarter IS NULL")
    op.execute("UPDATE lp_drawdowns SET forecast_next_quarter = 5.0 WHERE forecast_next_quarter IS NULL")
    op.execute("UPDATE lp_drawdowns SET forecast_next_quarter_period = 'Q2''25' WHERE forecast_next_quarter_period IS NULL")
    
    # Now make the new columns non-nullable
    op.alter_column('lp_drawdowns', 'status', nullable=False)
    op.alter_column('lp_drawdowns', 'drawdown_quarter', nullable=False)
    op.alter_column('lp_drawdowns', 'forecast_next_quarter', nullable=False)
    op.alter_column('lp_drawdowns', 'forecast_next_quarter_period', nullable=False)


def downgrade():
    # Remove new columns from lp_drawdowns
    op.drop_column('lp_drawdowns', 'stamp_duty')
    op.drop_column('lp_drawdowns', 'mgmt_fees')
    op.drop_column('lp_drawdowns', 'date_of_allotment')
    op.drop_column('lp_drawdowns', 'nav_value')
    op.drop_column('lp_drawdowns', 'allotted_units')
    op.drop_column('lp_drawdowns', 'amt_accepted')
    op.drop_column('lp_drawdowns', 'status')
    op.drop_column('lp_drawdowns', 'forecast_next_quarter_period')
    op.drop_column('lp_drawdowns', 'forecast_next_quarter')
    op.drop_column('lp_drawdowns', 'remaining_commitment')
    op.drop_column('lp_drawdowns', 'amount_called_up')
    op.drop_column('lp_drawdowns', 'drawdown_amount')
    op.drop_column('lp_drawdowns', 'committed_amt')
    op.drop_column('lp_drawdowns', 'drawdown_quarter')
    op.drop_column('lp_drawdowns', 'drawdown_due_date')
    op.drop_column('lp_drawdowns', 'notice_date')
    
    # Recreate old columns
    op.add_column('lp_drawdowns', sa.Column('drawdown_date', sa.Date(), nullable=False))
    op.add_column('lp_drawdowns', sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False))
    op.add_column('lp_drawdowns', sa.Column('payment_due_date', sa.Date(), nullable=False))
    op.add_column('lp_drawdowns', sa.Column('payment_status', sa.String(length=50), nullable=False, default="Pending"))
    
    # Drop drawdown_notices table
    op.drop_table('drawdown_notices')