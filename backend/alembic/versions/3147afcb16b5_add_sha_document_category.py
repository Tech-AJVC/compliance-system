"""add_sha_document_category

Revision ID: 3147afcb16b5
Revises: afb8f2418ff2
Create Date: 2025-07-20 11:03:56.353245

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3147afcb16b5'
down_revision = 'afb8f2418ff2'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing check constraint
    op.execute('ALTER TABLE documents DROP CONSTRAINT IF EXISTS valid_document_category')
    
    # Create a new check constraint with SHA included
    op.execute('''
    ALTER TABLE documents ADD CONSTRAINT valid_document_category 
    CHECK (category IN ('Contribution Agreement', 'KYC', 'Notification', 'Report', 'Certificate', 'Information', 'Other', 'CML', 'Drawdown Notice', 'SHA'))
    ''')


def downgrade():
    # Drop the current constraint
    op.execute('ALTER TABLE documents DROP CONSTRAINT IF EXISTS valid_document_category')
    
    # Recreate the old constraint without SHA
    op.execute('''
    ALTER TABLE documents ADD CONSTRAINT valid_document_category 
    CHECK (category IN ('Contribution Agreement', 'KYC', 'Notification', 'Report', 'Certificate', 'Information', 'Other', 'CML', 'Drawdown Notice'))
    ''')
