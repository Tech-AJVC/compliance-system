from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Text, DateTime, text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database.base import Base
import uuid
from datetime import datetime

class LPDrawdown(Base):
    __tablename__ = "lp_drawdowns"

    drawdown_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fund_id = Column(Integer, ForeignKey("fund_details.fund_id"), nullable=False)
    lp_id = Column(UUID(as_uuid=True), ForeignKey("lp_details.lp_id"), nullable=False)
    
    # Core drawdown information
    notice_date = Column(Date, nullable=False)
    drawdown_due_date = Column(Date, nullable=False)
    drawdown_percentage = Column(Numeric(5, 2), nullable=False)  # UI input
    drawdown_quarter = Column(String(20), nullable=False)  # e.g., "Q1'25"
    
    # Calculated amounts (calculated at API level)
    committed_amt = Column(Numeric(15, 2), nullable=False)  # From LP details
    drawdown_amount = Column(Numeric(15, 2), nullable=False)  # percentage * committed_amt
    amount_called_up = Column(Numeric(15, 2), nullable=False)  # Sum of previous drawdowns
    remaining_commitment = Column(Numeric(15, 2), nullable=False)  # committed_amt - amount_called_up
    
    # Forecast information
    forecast_next_quarter = Column(Numeric(5, 2), nullable=False)  # UI input - percentage
    forecast_next_quarter_period = Column(String(20), nullable=False)  # e.g., "Q2'25 Jul-Sep"
    
    # Status tracking
    status = Column(String(50), nullable=False, default="Sent")  # Sent, Demat Pending, Wire Pending, etc.
    
    # Payment tracking
    payment_received_date = Column(Date, nullable=True)
    amt_accepted = Column(Numeric(15, 2), nullable=True)  # Amount actually received
    
    # Optional fields for advanced tracking
    allotted_units = Column(Integer, nullable=True)
    nav_value = Column(Numeric(10, 2), nullable=True)
    date_of_allotment = Column(Date, nullable=True)
    mgmt_fees = Column(Numeric(15, 2), nullable=True)
    stamp_duty = Column(Numeric(10, 2), nullable=True)
    
    # Metadata
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=datetime.now)

    # Relationships
    fund = relationship("FundDetails", back_populates="lp_drawdowns")
    lp = relationship("LPDetails", back_populates="drawdowns")
    drawdown_notices = relationship("DrawdownNotice", back_populates="drawdown")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.drawdown_id:
            self.drawdown_id = uuid.uuid4()


class DrawdownNotice(Base):
    __tablename__ = "drawdown_notices"

    notice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drawdown_id = Column(UUID(as_uuid=True), ForeignKey("lp_drawdowns.drawdown_id"), nullable=False)
    lp_id = Column(UUID(as_uuid=True), ForeignKey("lp_details.lp_id"), nullable=False)
    
    # Notice details
    notice_date = Column(Date, nullable=False)
    amount_due = Column(Numeric(18, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Document and delivery tracking
    pdf_file_path = Column(String(500), nullable=True)  # Path to generated PDF
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=True)
    
    # Delivery status
    status = Column(String(30), nullable=False, default='Generated')  # Generated, Sent, Failed, Viewed
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_channel = Column(String(30), nullable=True, default='email')
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=datetime.now)

    # Relationships
    drawdown = relationship("LPDrawdown", back_populates="drawdown_notices")
    lp = relationship("LPDetails")
    document = relationship("Document", foreign_keys=[document_id])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.notice_id:
            self.notice_id = uuid.uuid4()
