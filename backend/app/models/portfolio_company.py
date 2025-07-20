from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base
from datetime import datetime
import uuid


class PortfolioCompany(Base):
    __tablename__ = "portfolio_companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    startup_brand = Column(String(255), nullable=False, unique=True)
    company_name = Column(String(255), nullable=False, unique=True)
    sector = Column(String(100), nullable=True)
    product_description = Column(Text, nullable=True)
    registered_address = Column(Text, nullable=True)
    pan = Column(String(20), nullable=True)
    isin = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    # Relationships
    founders = relationship("PortfolioFounder", back_populates="company")
    investments = relationship("PortfolioInvestment", back_populates="company")
    documents = relationship("PortfolioDocument", back_populates="company") 