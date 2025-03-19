"""Add approver drive link column

Revision ID: a4e78dd581fb
Revises: ee02e213762d
Create Date: 2025-03-19 11:26:49.369911

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4e78dd581fb'
down_revision = 'ee02e213762d'
branch_labels = None
depends_on = None


def upgrade():
    # Add approver_drive_link column to documents table
    op.add_column('documents', sa.Column('approver_drive_link', sa.String(), nullable=True))


def downgrade():
    # Remove approver_drive_link column from documents table
    op.drop_column('documents', 'approver_drive_link')
