"""add_lp_documents_table_and_missing_lp_fields

Revision ID: aa68be80e5f3
Revises: b64e4dcae6fd
Create Date: 2025-06-29 12:55:27.443852

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'aa68be80e5f3'
down_revision = 'b64e4dcae6fd'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing fields to lp_details table
    op.add_column('lp_details', sa.Column('invested_fund_id', sa.Integer(), nullable=True))
    op.add_column('lp_details', sa.Column('email_for_drawdowns', sa.String(length=255), nullable=True))
    op.add_column('lp_details', sa.Column('kyc_status', sa.String(length=50), nullable=True))
    
    # Update the status column to have proper default and constraint
    op.alter_column('lp_details', 'status',
                    existing_type=sa.VARCHAR(length=50),
                    server_default='Waiting for KYC',
                    nullable=True)
    
    # Create lp_documents table
    op.create_table('lp_documents',
        sa.Column('lp_document_id', sa.UUID(), nullable=False, default=sa.text('uuid_generate_v4()')),
        sa.Column('lp_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lp_id'], ['lp_details.lp_id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ),
        sa.PrimaryKeyConstraint('lp_document_id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_lp_details_email_for_drawdowns', 'lp_details', ['email_for_drawdowns'])
    op.create_index('idx_lp_details_pan', 'lp_details', ['pan'])
    op.create_index('idx_lp_documents_lp_id', 'lp_documents', ['lp_id'])
    op.create_index('idx_lp_documents_document_type', 'lp_documents', ['document_type'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_lp_documents_document_type')
    op.drop_index('idx_lp_documents_lp_id') 
    op.drop_index('idx_lp_details_pan')
    op.drop_index('idx_lp_details_email_for_drawdowns')
    
    # Drop lp_documents table
    op.drop_table('lp_documents')
    
    # Remove added columns from lp_details
    op.drop_column('lp_details', 'kyc_status')
    op.drop_column('lp_details', 'email_for_drawdowns')
    op.drop_column('lp_details', 'invested_fund_id')
    
    # Revert status column changes
    op.alter_column('lp_details', 'status',
                    existing_type=sa.VARCHAR(length=50),
                    server_default=None,
                    nullable=True)
