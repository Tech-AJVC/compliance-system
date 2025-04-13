"""add_certificate_information_document_categories

Revision ID: 9a7d63c67d5b
Revises: b8dd2c8c0d06
Create Date: 2025-04-12 19:53:14.112005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a7d63c67d5b'
down_revision = 'b8dd2c8c0d06'
branch_labels = None
depends_on = None


def upgrade():
    # First drop the existing check constraint
    op.execute('ALTER TABLE documents DROP CONSTRAINT IF EXISTS valid_document_category')
    
    # Create a new check constraint with the updated categories
    op.execute('''
    ALTER TABLE documents ADD CONSTRAINT valid_document_category 
    CHECK (category IN ('Contribution Agreement', 'KYC', 'Notification', 'Report', 'Certificate', 'Information', 'Other'))
    ''')


def downgrade():
    # Drop the updated constraint
    op.execute('ALTER TABLE documents DROP CONSTRAINT IF EXISTS valid_document_category')
    
    # Restore the original constraint without the new categories
    op.execute('''
    ALTER TABLE documents ADD CONSTRAINT valid_document_category 
    CHECK (category IN ('Contribution Agreement', 'KYC', 'Notification', 'Report', 'Other'))
    ''')
