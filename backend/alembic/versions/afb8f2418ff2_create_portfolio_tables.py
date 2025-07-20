"""create_portfolio_tables

Revision ID: afb8f2418ff2
Revises: 25b909891eca
Create Date: 2025-07-20 09:48:33.434119

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'afb8f2418ff2'
down_revision = '25b909891eca'
branch_labels = None
depends_on = None


def upgrade():
    # Create portfolio_companies table
    op.create_table(
        'portfolio_companies',
        sa.Column('company_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('startup_brand', sa.String(length=255), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('product_description', sa.Text(), nullable=True),
        sa.Column('registered_address', sa.Text(), nullable=True),
        sa.Column('pan', sa.String(length=20), nullable=True),
        sa.Column('isin', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('company_id'),
        sa.UniqueConstraint('startup_brand'),
        sa.UniqueConstraint('company_name')
    )

    # Create portfolio_founders table
    op.create_table(
        'portfolio_founders',
        sa.Column('founder_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('founder_name', sa.String(length=255), nullable=False),
        sa.Column('founder_email', sa.String(length=255), nullable=False),
        sa.Column('founder_role', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['portfolio_companies.company_id'], ),
        sa.PrimaryKeyConstraint('founder_id'),
        sa.UniqueConstraint('founder_email')
    )

    # Create portfolio_investments table
    op.create_table(
        'portfolio_investments',
        sa.Column('investment_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('fund_id', sa.Integer(), nullable=False),
        sa.Column('amount_invested', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('termsheet_sign_date', sa.Date(), nullable=True),
        sa.Column('sha_sign_date', sa.Date(), nullable=True),
        sa.Column('funding_date', sa.Date(), nullable=False),
        sa.Column('funding_tat_days', sa.Integer(), nullable=True),
        sa.Column('latest_valuation', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('valuation_date', sa.Date(), nullable=True),
        sa.Column('ec_sign_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['portfolio_companies.company_id'], ),
        sa.ForeignKeyConstraint(['fund_id'], ['fund_details.fund_id'], ),
        sa.PrimaryKeyConstraint('investment_id')
    )

    # Create portfolio_documents table
    op.create_table(
        'portfolio_documents',
        sa.Column('portfolio_document_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('doc_link', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['portfolio_companies.company_id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ),
        sa.PrimaryKeyConstraint('portfolio_document_id')
    )

    # Create indexes for better performance
    op.create_index('idx_portfolio_founders_company_id', 'portfolio_founders', ['company_id'])
    op.create_index('idx_portfolio_investments_company_id', 'portfolio_investments', ['company_id'])
    op.create_index('idx_portfolio_investments_fund_id', 'portfolio_investments', ['fund_id'])
    op.create_index('idx_portfolio_investments_funding_date', 'portfolio_investments', ['funding_date'])
    op.create_index('idx_portfolio_documents_company_id', 'portfolio_documents', ['company_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_portfolio_documents_company_id', table_name='portfolio_documents')
    op.drop_index('idx_portfolio_investments_funding_date', table_name='portfolio_investments')
    op.drop_index('idx_portfolio_investments_fund_id', table_name='portfolio_investments')
    op.drop_index('idx_portfolio_investments_company_id', table_name='portfolio_investments')
    op.drop_index('idx_portfolio_founders_company_id', table_name='portfolio_founders')
    
    # Drop tables in reverse order to avoid foreign key constraint violations
    op.drop_table('portfolio_documents')
    op.drop_table('portfolio_investments')
    op.drop_table('portfolio_founders')
    op.drop_table('portfolio_companies')
