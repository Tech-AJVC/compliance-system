from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from ..database.base import Base

class FundEntity(Base):
    __tablename__ = "fund_entities"

    fund_entity_id = Column(Integer, primary_key=True, autoincrement=True)
    fund_id = Column(Integer, ForeignKey("fund_details.fund_id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.entity_id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # for primary entity if needed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    fund = relationship("FundDetails", back_populates="fund_entities")
    entity = relationship("Entity", back_populates="fund_entities") 