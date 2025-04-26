"""fix_task_category_constraint_name

Revision ID: 224814d90ff6
Revises: 131e10a705bd
Create Date: 2025-04-26 20:33:26.819867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '224814d90ff6'
down_revision = '131e10a705bd'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing check constraint if it exists (use the correct name 'valid_category')
    op.execute('ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_category')
    
    # Create a new check constraint with the updated categories
    op.execute('''
    ALTER TABLE compliance_tasks ADD CONSTRAINT valid_category 
    CHECK (category IN ('SEBI', 'RBI', 'IT/GST', 'LP', 'OTHER'))
    ''')


def downgrade():
    # Drop the updated constraint
    op.execute('ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_category')
    
    # Restore the original constraint without the new categories
    op.execute('''
    ALTER TABLE compliance_tasks ADD CONSTRAINT valid_category 
    CHECK (category IN ('SEBI', 'RBI', 'IT/GST'))
    ''')
