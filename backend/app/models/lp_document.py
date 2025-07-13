from sqlalchemy import Column, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database.base import Base
import uuid
from datetime import datetime


class LPDocument(Base):
    __tablename__ = "lp_documents"

    lp_document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lp_id = Column(UUID(as_uuid=True), ForeignKey("lp_details.lp_id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # KYC, CA, CML, Drawdown_Notice, etc.
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    # Relationships
    lp = relationship("LPDetails", back_populates="lp_documents")
    document = relationship("Document") 