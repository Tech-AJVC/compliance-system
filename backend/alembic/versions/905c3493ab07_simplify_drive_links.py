"""simplify_drive_links

Revision ID: 905c3493ab07
Revises: a4e78dd581fb
Create Date: 2025-03-19 18:46:50.674385

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '905c3493ab07'
down_revision = 'a4e78dd581fb'
branch_labels = None
depends_on = None


def upgrade():
    # Add a single drive_link column
    op.add_column('documents', sa.Column('drive_link', sa.String(), nullable=True))
    
    # Copy uploader_drive_link values to the new drive_link column
    op.execute(
        """
        UPDATE documents
        SET drive_link = uploader_drive_link
        WHERE uploader_drive_link IS NOT NULL
        """
    )
    
    # We're not dropping the old columns yet to allow for a smoother transition
    # They can be removed in a future migration once everything is working with the new approach


def downgrade():
    # Remove the new drive_link column
    op.drop_column('documents', 'drive_link')
