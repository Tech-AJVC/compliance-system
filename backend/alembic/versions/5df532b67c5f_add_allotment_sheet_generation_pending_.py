"""add_allotment_sheet_generation_pending_status

Revision ID: 5df532b67c5f
Revises: m3n4o5p6q7r8
Create Date: 2025-08-15 20:06:22.843956

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5df532b67c5f'
down_revision = 'm3n4o5p6q7r8'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new status constraint to LPDrawdown table
    op.create_check_constraint(
        'valid_lp_drawdown_status',
        'lp_drawdowns',
        "status IN ('Drawdown Payment Pending', 'Allotment Pending', 'Allotment Sheet Generation Pending', 'Allotment Done')"
    )
    
    # Update the DrawdownNotice constraint to include the new status
    op.execute("ALTER TABLE drawdown_notices DROP CONSTRAINT IF EXISTS valid_drawdown_notice_status;")
    op.create_check_constraint(
        'valid_drawdown_notice_status',
        'drawdown_notices',
        "status IN ('Drawdown Payment Pending', 'Allotment Pending', 'Allotment Sheet Generation Pending', 'Allotment Done')"
    )


def downgrade():
    # Remove the LPDrawdown status constraint
    op.drop_constraint('valid_lp_drawdown_status', 'lp_drawdowns', type_='check')
    
    # Revert DrawdownNotice constraint to original status values
    op.execute("ALTER TABLE drawdown_notices DROP CONSTRAINT IF EXISTS valid_drawdown_notice_status;")
    op.create_check_constraint(
        'valid_drawdown_notice_status',
        'drawdown_notices',
        "status IN ('Drawdown Payment Pending', 'Allotment Pending', 'Allotment Done')"
    )
