"""remove_invested_fund_id_column

Revision ID: 68821077da38
Revises: f4f27c34893f
Create Date: 2025-06-29 21:27:36.573521

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '68821077da38'
down_revision = 'aa68be80e5f3'
branch_labels = None
depends_on = None


def upgrade():
    # Remove invested_fund_id column from lp_details table
    # Check if column exists first to avoid errors
    op.drop_column('lp_details', 'invested_fund_id')


def downgrade():
    # Add back invested_fund_id column if we need to rollback
    op.add_column('lp_details', sa.Column('invested_fund_id', sa.Integer(), nullable=True))
