"""add_lp_other_task_categories

Revision ID: 131e10a705bd
Revises: 781287a0a8d4
Create Date: 2025-04-12 21:44:24.740705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '131e10a705bd'
down_revision = '781287a0a8d4'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing check constraint if it exists
    op.execute('ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_task_category')
    
    # Create a new check constraint with the updated categories
    op.execute('''
    ALTER TABLE compliance_tasks ADD CONSTRAINT valid_task_category 
    CHECK (category IN ('SEBI', 'RBI', 'IT/GST', 'LP', 'Other'))
    ''')


def downgrade():
    # Drop the updated constraint
    op.execute('ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_task_category')
    
    # Restore the original constraint without the new categories
    op.execute('''
    ALTER TABLE compliance_tasks ADD CONSTRAINT valid_task_category 
    CHECK (category IN ('SEBI', 'RBI', 'IT/GST'))
    ''')
