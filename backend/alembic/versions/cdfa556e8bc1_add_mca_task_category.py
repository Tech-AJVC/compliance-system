"""add_mca_task_category

Revision ID: cdfa556e8bc1
Revises: 224814d90ff6
Create Date: 2025-05-12 21:28:43.535805

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cdfa556e8bc1'
down_revision = '224814d90ff6'
branch_labels = None
depends_on = None


def upgrade():
    # Add MCA to the valid_category constraint
    op.execute(
        "ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_category;"
    )
    op.execute(
        "ALTER TABLE compliance_tasks ADD CONSTRAINT valid_category CHECK "
        "(category IN ('SEBI', 'RBI', 'IT/GST', 'LP', 'OTHER', 'MCA'));"
    )


def downgrade():
    # Remove MCA from the valid_category constraint
    op.execute(
        "ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_category;"
    )
    op.execute(
        "ALTER TABLE compliance_tasks ADD CONSTRAINT valid_category CHECK "
        "(category IN ('SEBI', 'RBI', 'IT/GST', 'LP', 'OTHER'));"
    )
