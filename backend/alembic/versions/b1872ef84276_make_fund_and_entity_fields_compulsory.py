"""make_fund_and_entity_fields_compulsory

Revision ID: b1872ef84276
Revises: 3328ca9d857f
Create Date: 2025-06-26 23:33:24.558603

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1872ef84276'
down_revision = '3328ca9d857f'
branch_labels = None
depends_on = None


def upgrade():
    # Update Entity table - make basic fields NOT NULL
    op.alter_column('entities', 'entity_name', nullable=False)
    op.alter_column('entities', 'entity_address', nullable=False)
    op.alter_column('entities', 'entity_telephone', nullable=False)
    op.alter_column('entities', 'entity_email', nullable=False)
    op.alter_column('entities', 'entity_poc', nullable=False)
    
    # Update Fund Details table - make required fields NOT NULL
    op.alter_column('fund_details', 'scheme_structure_type', nullable=False)
    op.alter_column('fund_details', 'custodian_name', nullable=False)
    op.alter_column('fund_details', 'rta_name', nullable=False)
    op.alter_column('fund_details', 'compliance_officer_name', nullable=False)
    op.alter_column('fund_details', 'compliance_officer_email', nullable=False)
    op.alter_column('fund_details', 'compliance_officer_phone', nullable=False)
    op.alter_column('fund_details', 'investment_officer_name', nullable=False)
    op.alter_column('fund_details', 'investment_officer_designation', nullable=False)
    op.alter_column('fund_details', 'investment_officer_pan', nullable=False)
    op.alter_column('fund_details', 'investment_officer_din', nullable=False)
    op.alter_column('fund_details', 'date_of_appointment', nullable=False)
    op.alter_column('fund_details', 'scheme_pan', nullable=False)
    op.alter_column('fund_details', 'nav', nullable=False)
    op.alter_column('fund_details', 'target_fund_size', nullable=False)
    op.alter_column('fund_details', 'date_final_draft_ppm', nullable=False)
    op.alter_column('fund_details', 'date_sebi_ppm_comm', nullable=False)
    op.alter_column('fund_details', 'date_launch_of_scheme', nullable=False)
    op.alter_column('fund_details', 'date_initial_close', nullable=False)
    op.alter_column('fund_details', 'date_final_close', nullable=False)
    op.alter_column('fund_details', 'commitment_initial_close_cr', nullable=False)
    op.alter_column('fund_details', 'terms_end_date', nullable=False)
    op.alter_column('fund_details', 'bank_name', nullable=False)
    op.alter_column('fund_details', 'bank_ifsc', nullable=False)
    op.alter_column('fund_details', 'bank_account_name', nullable=False)
    op.alter_column('fund_details', 'bank_account_no', nullable=False)
    op.alter_column('fund_details', 'bank_contact_person', nullable=False)
    op.alter_column('fund_details', 'bank_contact_phone', nullable=False)
    
    # Add enum constraints for fund categorical fields
    op.create_check_constraint(
        'valid_scheme_status',
        'fund_details',
        "scheme_status IN ('Active', 'Inactive')"
    )
    
    op.create_check_constraint(
        'valid_legal_structure',
        'fund_details',
        "legal_structure IN ('Trust', 'Company', 'LLP')"
    )
    
    op.create_check_constraint(
        'valid_scheme_structure',
        'fund_details',
        "scheme_structure_type IN ('Close Ended', 'Open Ended')"
    )
    
    op.create_check_constraint(
        'valid_category_subcategory',
        'fund_details',
        "category_subcategory IN ('Category I AIF', 'Category II AIF', 'Category III AIF')"
    )


def downgrade():
    # Remove constraints
    op.drop_constraint('valid_scheme_status', 'fund_details')
    op.drop_constraint('valid_legal_structure', 'fund_details')
    op.drop_constraint('valid_scheme_structure', 'fund_details')
    op.drop_constraint('valid_category_subcategory', 'fund_details')
    
    # Revert Entity table changes
    op.alter_column('entities', 'entity_name', nullable=True)
    op.alter_column('entities', 'entity_address', nullable=True)
    op.alter_column('entities', 'entity_telephone', nullable=True)
    op.alter_column('entities', 'entity_email', nullable=True)
    op.alter_column('entities', 'entity_poc', nullable=True)
    
    # Revert Fund Details table changes
    op.alter_column('fund_details', 'scheme_structure_type', nullable=True)
    op.alter_column('fund_details', 'custodian_name', nullable=True)
    op.alter_column('fund_details', 'rta_name', nullable=True)
    op.alter_column('fund_details', 'compliance_officer_name', nullable=True)
    op.alter_column('fund_details', 'compliance_officer_email', nullable=True)
    op.alter_column('fund_details', 'compliance_officer_phone', nullable=True)
    op.alter_column('fund_details', 'investment_officer_name', nullable=True)
    op.alter_column('fund_details', 'investment_officer_designation', nullable=True)
    op.alter_column('fund_details', 'investment_officer_pan', nullable=True)
    op.alter_column('fund_details', 'investment_officer_din', nullable=True)
    op.alter_column('fund_details', 'date_of_appointment', nullable=True)
    op.alter_column('fund_details', 'scheme_pan', nullable=True)
    op.alter_column('fund_details', 'nav', nullable=True)
    op.alter_column('fund_details', 'target_fund_size', nullable=True)
    op.alter_column('fund_details', 'date_final_draft_ppm', nullable=True)
    op.alter_column('fund_details', 'date_sebi_ppm_comm', nullable=True)
    op.alter_column('fund_details', 'date_launch_of_scheme', nullable=True)
    op.alter_column('fund_details', 'date_initial_close', nullable=True)
    op.alter_column('fund_details', 'date_final_close', nullable=True)
    op.alter_column('fund_details', 'commitment_initial_close_cr', nullable=True)
    op.alter_column('fund_details', 'terms_end_date', nullable=True)
    op.alter_column('fund_details', 'bank_name', nullable=True)
    op.alter_column('fund_details', 'bank_ifsc', nullable=True)
    op.alter_column('fund_details', 'bank_account_name', nullable=True)
    op.alter_column('fund_details', 'bank_account_no', nullable=True)
    op.alter_column('fund_details', 'bank_contact_person', nullable=True)
    op.alter_column('fund_details', 'bank_contact_phone', nullable=True)
