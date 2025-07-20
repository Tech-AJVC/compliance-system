from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base
from datetime import datetime


class PortfolioFounder(Base):
    __tablename__ = "portfolio_founders"

    founder_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("portfolio_companies.company_id"), nullable=False)
    founder_name = Column(String(255), nullable=False)
    founder_email = Column(String(255), nullable=False, unique=True)
    founder_role = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    # Relationships
    company = relationship("PortfolioCompany", back_populates="founders") 