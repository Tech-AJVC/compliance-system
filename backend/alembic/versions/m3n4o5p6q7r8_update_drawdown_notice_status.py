"""update_drawdown_notice_status

Revision ID: 003_update_drawdown_notice_status
Revises: 002_create_unit_allotments_table
Create Date: 2025-01-27 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'm3n4o5p6q7r8'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing constraint if it exists
    op.execute("ALTER TABLE drawdown_notices DROP CONSTRAINT IF EXISTS valid_drawdown_notice_status")
    
    # Update default status for new records
    op.alter_column('drawdown_notices', 'status',
                    existing_type=sa.String(30),
                    type_=sa.String(40),
                    server_default='Drawdown Payment Pending',
                    nullable=False)
    
    # Update existing records with old status values to new ones
    op.execute("""
        UPDATE drawdown_notices 
        SET status = CASE 
            WHEN status = 'Generated' THEN 'Drawdown Payment Pending'
            WHEN status = 'Sent' THEN 'Drawdown Payment Pending'
            WHEN status = 'Failed' THEN 'Drawdown Payment Pending'
            WHEN status = 'Viewed' THEN 'Drawdown Payment Pending'
            ELSE status 
        END
    """)
    
    # Add new constraint with valid status values
    op.execute("""
        ALTER TABLE drawdown_notices 
        ADD CONSTRAINT valid_drawdown_notice_status 
        CHECK (status IN ('Drawdown Payment Pending', 'Allotment Pending', 'Allotment Done'))
    """)


def downgrade():
    # Drop new constraint
    op.execute("ALTER TABLE drawdown_notices DROP CONSTRAINT IF EXISTS valid_drawdown_notice_status")
    
    # Revert status values back to old ones
    op.execute("""
        UPDATE drawdown_notices 
        SET status = CASE 
            WHEN status = 'Drawdown Payment Pending' THEN 'Generated'
            WHEN status = 'Allotment Pending' THEN 'Sent'
            WHEN status = 'Allotment Done' THEN 'Viewed'
            ELSE 'Generated'
        END
    """)
    
    # Revert column changes
    op.alter_column('drawdown_notices', 'status',
                    existing_type=sa.String(40),
                    type_=sa.String(30),
                    server_default='Generated',
                    nullable=False)