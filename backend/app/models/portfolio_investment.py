from sqlalchemy import Column, Integer, BigInteger, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base
from datetime import datetime


class PortfolioInvestment(Base):
    __tablename__ = "portfolio_investments"

    investment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("portfolio_companies.company_id"), nullable=False)
    fund_id = Column(Integer, ForeignKey("fund_details.fund_id"), nullable=False)
    amount_invested = Column(Numeric(18, 2), nullable=False)
    termsheet_sign_date = Column(Date, nullable=True)
    sha_sign_date = Column(Date, nullable=True)
    funding_date = Column(Date, nullable=False)
    funding_tat_days = Column(Integer, nullable=True)  # Calculated: funding_date - termsheet_sign_date
    latest_valuation = Column(Numeric(18, 2), nullable=True)
    valuation_date = Column(Date, nullable=True)
    ec_sign_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    # Relationships
    company = relationship("PortfolioCompany", back_populates="investments")
    # Note: fund relationship will be added when fund_details model is available 