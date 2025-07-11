"""add_lp_documents_table_and_missing_lp_fields

Revision ID: b5b3c4de80d4
Revises: 68821077da38
Create Date: 2025-07-09 22:30:46.479610

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5b3c4de80d4'
down_revision = '68821077da38'
branch_labels = None
depends_on = None


def upgrade():
    # Create lp_documents table
    op.create_table('lp_documents',
        sa.Column('lp_document_id', sa.UUID(), nullable=False),
        sa.Column('lp_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], name='lp_documents_document_id_fkey'),
        sa.ForeignKeyConstraint(['lp_id'], ['lp_details.lp_id'], name='lp_documents_lp_id_fkey'),
        sa.PrimaryKeyConstraint('lp_document_id', name='lp_documents_pkey')
    )
    
    # Add missing fields to lp_details table
    op.add_column('lp_details', sa.Column('kyc_status', sa.String(length=20), nullable=True))


def downgrade():
    # Remove added columns from lp_details table
    op.drop_column('lp_details', 'kyc_status')
    
    # Drop lp_documents table
    op.drop_table('lp_documents')
