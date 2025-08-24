from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Text, DateTime, Integer, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database.base import Base
import uuid
import enum
from datetime import datetime

class LPPaymentStatus(str, enum.Enum):
    """Enum for LP payment status values"""
    PENDING = "Pending"
    PAID = "Paid"
    SHORTFALL = "Shortfall"
    OVER_PAYMENT = "Over-payment"

class LPPayment(Base):
    __tablename__ = "lp_payments"

    lp_payment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    lp_id = Column(UUID(as_uuid=True), ForeignKey("lp_details.lp_id"), nullable=False)
    drawdown_id = Column(UUID(as_uuid=True), ForeignKey("lp_drawdowns.drawdown_id"), nullable=False)
    payment_id = Column(BigInteger, ForeignKey("payment_reconciliation.payment_id"), nullable=True)  # FK to PaymentReconciliation
    paid_amount = Column(Numeric(18, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    fund_id = Column(Integer, ForeignKey("fund_details.fund_id"), nullable=False)
    quarter = Column(String(15), nullable=False)
    amount_due = Column(Numeric(18, 2), nullable=False)
    status = Column(String(20), nullable=False, default=LPPaymentStatus.PENDING.value)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lp = relationship("LPDetails", back_populates="payments")
    drawdown = relationship("LPDrawdown", back_populates="payments")
    fund = relationship("FundDetails", back_populates="lp_payments")
    payment_reconciliation = relationship("PaymentReconciliation", back_populates="lp_payments") 