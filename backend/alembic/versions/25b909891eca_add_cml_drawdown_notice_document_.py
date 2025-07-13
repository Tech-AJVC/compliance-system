"""add_cml_drawdown_notice_document_categories

Revision ID: 25b909891eca
Revises: b5b3c4de80d4
Create Date: 2025-07-09 22:31:28.029769

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25b909891eca'
down_revision = 'b5b3c4de80d4'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing check constraint
    op.execute('ALTER TABLE documents DROP CONSTRAINT IF EXISTS valid_document_category')
    
    # Create a new check constraint with the updated categories including CML and Drawdown Notice
    op.execute('''
    ALTER TABLE documents ADD CONSTRAINT valid_document_category 
    CHECK (category IN ('Contribution Agreement', 'KYC', 'Notification', 'Report', 'Certificate', 'Information', 'Other', 'CML', 'Drawdown Notice'))
    ''')


def downgrade():
    # Drop the updated constraint
    op.execute('ALTER TABLE documents DROP CONSTRAINT IF EXISTS valid_document_category')
    
    # Restore the original constraint without CML and Drawdown Notice
    op.execute('''
    ALTER TABLE documents ADD CONSTRAINT valid_document_category 
    CHECK (category IN ('Contribution Agreement', 'KYC', 'Notification', 'Report', 'Certificate', 'Information', 'Other'))
    ''')
