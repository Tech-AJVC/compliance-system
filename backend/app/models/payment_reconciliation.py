from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Integer, BigInteger
from sqlalchemy.orm import relationship
from ..database.base import Base
import enum
from datetime import datetime

class PaymentReconciliationStatus(str, enum.Enum):
    """Enum for payment reconciliation status values"""
    IN_PROGRESS = "In-Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"

class PaymentReconciliation(Base):
    __tablename__ = "payment_reconciliation"

    payment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_s3_link = Column(String(200), nullable=True)
    fund_id = Column(Integer, ForeignKey("fund_details.fund_id"), nullable=False)
    drawdown_quarter = Column(String(15), nullable=False)
    total_expected = Column(Numeric(18, 2), nullable=False)
    total_received = Column(Numeric(18, 2), nullable=False)
    overall_status = Column(String(20), nullable=False, default=PaymentReconciliationStatus.IN_PROGRESS.value)
    processed_payments = Column(Integer, nullable=False, default=0)
    matched_payments = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fund = relationship("FundDetails", back_populates="payment_reconciliations")
    lp_payments = relationship("LPPayment", back_populates="payment_reconciliation") 