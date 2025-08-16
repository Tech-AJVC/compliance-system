from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, DECIMAL, func, Text, CheckConstraint
from sqlalchemy.orm import relationship
from ..database.base import Base

class FundDetails(Base):
    __tablename__ = "fund_details"

    fund_id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_name = Column(String(255), nullable=False, unique=True)
    scheme_status = Column(String(40), nullable=False)  # Active / Inactive
    aif_name = Column(String(255), nullable=False)
    aif_pan = Column(String(20), nullable=False, unique=True)
    aif_registration_no = Column(String(50), nullable=False)
    legal_structure = Column(String(50), nullable=False)  # Trust / LLP / Company
    category_subcategory = Column(String(100), nullable=False)  # Category I/II/III AIF
    scheme_structure_type = Column(String(40), nullable=False)  # Close Ended / Open Ended - Now compulsory
    
    # Fund management details - now compulsory
    custodian_name = Column(String(255), nullable=False)
    rta_name = Column(String(255), nullable=False)
    compliance_officer_name = Column(String(255), nullable=False)
    compliance_officer_email = Column(String(255), nullable=False)
    compliance_officer_phone = Column(String(20), nullable=False)
    investment_officer_name = Column(String(255), nullable=False)
    investment_officer_designation = Column(String(100), nullable=False)  # Fund Manager
    investment_officer_pan = Column(String(20), nullable=False)
    investment_officer_din = Column(String(20), nullable=False)
    date_of_appointment = Column(Date, nullable=False)
    
    # Scheme details - now compulsory
    scheme_pan = Column(String(20), nullable=False)  # duplicate of aif_pan but kept for template parity
    nav = Column(Integer, nullable=False, default=100)  # NAV per unit (typically 100)
    mgmt_fee_rate = Column(DECIMAL(5,4), nullable=False, default=0.01)  # 1% management fee rate
    stamp_duty_rate = Column(DECIMAL(8,7), nullable=False, default=0.00005)  # 0.005% stamp duty rate
    target_fund_size = Column(DECIMAL(18,2), nullable=False)
    
    # Important dates - now compulsory
    date_final_draft_ppm = Column(Date, nullable=False)
    date_sebi_ppm_comm = Column(Date, nullable=False)
    date_launch_of_scheme = Column(Date, nullable=False)
    date_initial_close = Column(Date, nullable=False)
    date_final_close = Column(Date, nullable=False)
    commitment_initial_close_cr = Column(DECIMAL(18,2), nullable=False)  # in Crores
    terms_end_date = Column(Date, nullable=False)
    
    # Bank details - now compulsory
    bank_name = Column(String(255), nullable=False)
    bank_ifsc = Column(String(15), nullable=False)
    bank_account_name = Column(String(255), nullable=False)
    bank_account_no = Column(String(50), nullable=False, unique=True)
    bank_contact_person = Column(String(255), nullable=False)
    bank_contact_phone = Column(String(20), nullable=False)
    
    # Optional fields
    entity_type = Column(String(50), nullable=True)  # MANAGER / SPONSOR etc.
    entity_name = Column(String(255), nullable=True)
    entity_pan = Column(String(20), nullable=True)
    entity_email = Column(String(255), nullable=True)
    entity_address = Column(Text, nullable=True)
    extension_permitted = Column(Boolean, nullable=True)
    extended_end_date = Column(Date, nullable=True)
    greenshoe_option = Column(DECIMAL(18,2), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add enum constraints for categorical fields
    __table_args__ = (
        CheckConstraint(
            scheme_status.in_(['Active', 'Inactive']),
            name='valid_scheme_status'
        ),
        CheckConstraint(
            legal_structure.in_(['Trust', 'Company', 'LLP']),
            name='valid_legal_structure'
        ),
        CheckConstraint(
            scheme_structure_type.in_(['Close Ended', 'Open Ended']),
            name='valid_scheme_structure'
        ),
        CheckConstraint(
            category_subcategory.in_(['Category I AIF', 'Category II AIF', 'Category III AIF']),
            name='valid_category_subcategory'
        ),
    )

    # Relationships
    fund_entities = relationship("FundEntity", back_populates="fund")
    lp_details = relationship("LPDetails", back_populates="fund")
    lp_drawdowns = relationship("LPDrawdown", back_populates="fund")
    unit_allotments = relationship("UnitAllotment", back_populates="fund") 