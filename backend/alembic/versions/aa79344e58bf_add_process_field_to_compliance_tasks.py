"""add_process_field_to_compliance_tasks

Revision ID: aa79344e58bf
Revises: e476f7a3b913
Create Date: 2025-08-24 12:14:14.841631

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa79344e58bf'
down_revision = 'e476f7a3b913'
branch_labels = None
depends_on = None


def upgrade():
    # Add process column to compliance_tasks table
    op.add_column('compliance_tasks', sa.Column('process', sa.String(), nullable=True))
    
    # Add check constraint for valid process values
    op.create_check_constraint(
        'valid_task_process',
        'compliance_tasks',
        "process IN ('LP Onboarding', 'Drawdown', 'Unit Allotment', 'invi Filing', 'Portfolio Onboarding', 'Entity Onboarding', 'SEBI Activity Report', 'Fund Registration', 'Monthly IT/GST Filings', 'Annual IT/GST Filings', 'Annual MCA Filings')"
    )


def downgrade():
    # Drop the check constraint first
    op.drop_constraint('valid_task_process', 'compliance_tasks', type_='check')
    
    # Drop the process column
    op.drop_column('compliance_tasks', 'process')
