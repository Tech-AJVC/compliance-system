"""Add drive link columns to document table

Revision ID: 30fe04078819
Revises: b842033d4078
Create Date: 2025-03-18 23:33:21.851036

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '30fe04078819'
down_revision = 'b842033d4078'
branch_labels = None
depends_on = None


def upgrade():
    # This migration is replaced by ee02e213762d
    pass


def downgrade():
    # This migration is replaced by ee02e213762d
    pass
