from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base
from datetime import datetime


class PortfolioDocument(Base):
    __tablename__ = "portfolio_documents"

    portfolio_document_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("portfolio_companies.company_id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # SHA, Term_Sheet, EC, Valuation_Report, Employment Agreement, SSA etc.
    doc_link = Column(String(255), nullable=True)  # Document link/URL
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    # Relationships
    company = relationship("PortfolioCompany", back_populates="documents")
    # Note: document relationship will be added when documents model is available 