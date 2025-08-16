from sqlalchemy import Column, Integer, String, Date, DECIMAL, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database.base import Base

class UnitAllotment(Base):
    __tablename__ = "unit_allotments"

    allotment_id = Column(Integer, primary_key=True, autoincrement=True)
    drawdown_id = Column(UUID(as_uuid=True), ForeignKey("lp_drawdowns.drawdown_id"), nullable=False)
    lp_id = Column(UUID(as_uuid=True), ForeignKey("lp_details.lp_id"), nullable=False)
    fund_id = Column(Integer, ForeignKey("fund_details.fund_id"), nullable=False)
    
    # Depository and holder information
    clid = Column(String(60), nullable=True)
    depository = Column(String(60), nullable=True)
    dpid = Column(String(20), nullable=True)
    first_holder_name = Column(String(255), nullable=False)
    first_holder_pan = Column(String(20), nullable=True)
    second_holder_name = Column(String(255), nullable=True)
    second_holder_pan = Column(String(20), nullable=True)
    third_holder_name = Column(String(255), nullable=True)
    third_holder_pan = Column(String(20), nullable=True)
    
    # Financial calculations
    mgmt_fees = Column(DECIMAL(18,2), nullable=False)
    committed_amt = Column(DECIMAL(18,2), nullable=False)
    amt_accepted = Column(DECIMAL(18,2), nullable=False)
    drawdown_amount = Column(DECIMAL(18,2), nullable=False)
    nav_value = Column(Integer, nullable=False)  # NAV as integer
    allotted_units = Column(Integer, nullable=False)
    stamp_duty = Column(DECIMAL(10,2), nullable=False)
    
    # Dates and quarter information
    drawdown_date = Column(Date, nullable=False)
    drawdown_quarter = Column(String(20), nullable=False)
    date_of_allotment = Column(Date, nullable=True)
    
    # Bank information
    bank_account_no = Column(String(50), nullable=True)
    bank_account_name = Column(String(255), nullable=True)
    bank_ifsc = Column(String(15), nullable=True)
    micr_code = Column(String(50), nullable=True)
    
    # Status and file tracking
    status = Column(String(40), nullable=False, default="Generated")
    excel_file_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    drawdown = relationship("LPDrawdown", back_populates="unit_allotments")
    lp = relationship("LPDetails", back_populates="unit_allotments")
    fund = relationship("FundDetails", back_populates="unit_allotments")

    def __repr__(self):
        return f"<UnitAllotment(allotment_id={self.allotment_id}, lp_name='{self.first_holder_name}', units={self.allotted_units})>"