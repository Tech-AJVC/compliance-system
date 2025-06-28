from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, func, CheckConstraint
from sqlalchemy.orm import relationship
from ..database.base import Base

class Entity(Base):
    __tablename__ = "entities"

    entity_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    entity_name = Column(String(255), nullable=False)  # Now compulsory
    entity_pan = Column(String(20), nullable=False)
    entity_address = Column(String, nullable=False)  # Now compulsory
    entity_telephone = Column(String(20), nullable=False)  # Now compulsory
    entity_email = Column(String(255), nullable=False)  # Now compulsory
    entity_poc = Column(String(255), nullable=False)  # Now compulsory - Point of Contact
    entity_registration_number = Column(String(100), nullable=True)
    entity_tan = Column(String(20), nullable=True)
    entity_date_of_incorporation = Column(Date, nullable=True)
    entity_gst_number = Column(String(30), nullable=True)
    entity_poc_din = Column(String(20), nullable=True)  # Director Identification Number
    entity_poc_pan = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add constraint for valid entity types
    __table_args__ = (
        CheckConstraint(
            entity_type.in_([
                'Manager', 'Sponsor', 'Trust', 'Custodian', 'RTA', 
                'Trustee', 'Auditor', 'Merchant Banker', 'Legal Advisor', 
                'Compliance Officer', 'Accountant', 'Tax'
            ]),
            name='valid_entity_type'
        ),
    )

    # Relationships
    fund_entities = relationship("FundEntity", back_populates="entity") 