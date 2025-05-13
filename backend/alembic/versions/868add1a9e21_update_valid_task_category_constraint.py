"""update_valid_task_category_constraint

Revision ID: 868add1a9e21
Revises: cdfa556e8bc1
Create Date: 2025-05-13 21:52:16.778963

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '868add1a9e21'
down_revision = 'cdfa556e8bc1'
branch_labels = None
depends_on = None


def upgrade():
    # Add MCA to the valid_task_category constraint
    op.execute(
        "ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_task_category;"
    )
    op.execute(
        "ALTER TABLE compliance_tasks ADD CONSTRAINT valid_task_category CHECK "
        "(category IN ('SEBI', 'RBI', 'IT/GST', 'LP', 'OTHER', 'MCA'));"
    )


def downgrade():
    # Remove MCA from the valid_task_category constraint
    op.execute(
        "ALTER TABLE compliance_tasks DROP CONSTRAINT IF EXISTS valid_task_category;"
    )
    op.execute(
        "ALTER TABLE compliance_tasks ADD CONSTRAINT valid_task_category CHECK "
        "(category IN ('SEBI', 'RBI', 'IT/GST', 'LP', 'OTHER'));"
    )
