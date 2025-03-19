"""Add google drive link columns

Revision ID: ee02e213762d
Revises: 30fe04078819
Create Date: 2025-03-18 23:35:02.624519

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee02e213762d'
down_revision = '30fe04078819'
branch_labels = None
depends_on = None


def upgrade():
    # Add Google Drive related columns to the documents table
    op.add_column('documents', sa.Column('drive_file_id', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('uploader_drive_link', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('assignee_drive_link', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('reviewer_drive_link', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('fund_manager_drive_link', sa.String(), nullable=True))


def downgrade():
    # Remove Google Drive related columns from the documents table
    op.drop_column('documents', 'fund_manager_drive_link')
    op.drop_column('documents', 'reviewer_drive_link')
    op.drop_column('documents', 'assignee_drive_link')
    op.drop_column('documents', 'uploader_drive_link')
    op.drop_column('documents', 'drive_file_id')
