from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..database.base import get_db
from ..models.fund_details import FundDetails
from ..models.fund_entity import FundEntity
from ..models.entity import Entity
from ..models.user import User
from ..schemas.fund import FundEntityCreate, FundEntityResponse
from ..schemas.entity import EntityResponse
from ..utils.audit import log_activity
from ..auth.security import get_current_user

router = APIRouter(prefix="/fund-entities", tags=["fund-entities"])

@router.post("/", response_model=FundEntityResponse, status_code=201)
def create_fund_entity_relationship(
    relationship_data: FundEntityCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Link an entity to a fund"""
    # Verify fund exists
    fund = db.query(FundDetails).filter(FundDetails.fund_id == relationship_data.fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    # Verify entity exists
    entity = db.query(Entity).filter(Entity.entity_id == relationship_data.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Check if relationship already exists
    existing = db.query(FundEntity).filter(
        FundEntity.fund_id == relationship_data.fund_id,
        FundEntity.entity_id == relationship_data.entity_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Entity {entity.entity_type} is already linked to this fund"
        )
    
    try:
        # Create relationship
        db_relationship = FundEntity(**relationship_data.model_dump())
        db.add(db_relationship)
        db.commit()
        db.refresh(db_relationship)
        
        # Get user_id for audit logging
        user_id = None
        if "sub" in current_user:
            user = db.query(User).filter(User.email == current_user["sub"]).first()
            if user:
                user_id = user.user_id
        
        # Log activity
        log_activity(
            db=db,
            user_id=user_id,
            activity="Fund-Entity Linked",
            details=f"Linked {entity.entity_type} to fund {fund.scheme_name}"
        )
        
        # Load entity details for response
        db_relationship.entity_details = entity
        
        return db_relationship
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating relationship: {str(e)}")

@router.get("/", response_model=List[FundEntityResponse])
def list_fund_entities(
    fund_id: int = Query(None, description="Filter by fund ID"),
    entity_id: int = Query(None, description="Filter by entity ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List fund-entity relationships with optional filtering"""
    query = db.query(FundEntity).options(joinedload(FundEntity.entity))
    
    if fund_id:
        query = query.filter(FundEntity.fund_id == fund_id)
    
    if entity_id:
        query = query.filter(FundEntity.entity_id == entity_id)
    
    relationships = query.all()
    
    # Add entity details to response
    for rel in relationships:
        rel.entity_details = rel.entity
    
    return relationships

@router.get("/funds/{fund_id}/entities", response_model=List[FundEntityResponse])
def get_fund_entities(
    fund_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all entities linked to a specific fund"""
    # Verify fund exists
    fund = db.query(FundDetails).filter(FundDetails.fund_id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    relationships = db.query(FundEntity).options(joinedload(FundEntity.entity)).filter(
        FundEntity.fund_id == fund_id
    ).all()
    
    # Add entity details to response
    for rel in relationships:
        rel.entity_details = rel.entity
    
    return relationships

@router.put("/funds/{fund_id}/entities/{entity_id}", response_model=FundEntityResponse)
def update_fund_entity_relationship(
    fund_id: int,
    entity_id: int,
    is_primary: bool = Query(False, description="Set as primary entity"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update primary status for a fund-entity relationship"""
    relationship = db.query(FundEntity).filter(
        FundEntity.fund_id == fund_id,
        FundEntity.entity_id == entity_id
    ).first()
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Fund-entity relationship not found")
    
    try:
        # Update relationship
        relationship.is_primary = is_primary
        
        db.commit()
        db.refresh(relationship)
        
        # Get user_id for audit logging
        user_id = None
        if "sub" in current_user:
            user = db.query(User).filter(User.email == current_user["sub"]).first()
            if user:
                user_id = user.user_id
        
        # Log activity
        log_activity(
            db=db,
            user_id=user_id,
            activity="Fund-Entity Updated",
            details=f"Updated entity primary status to: {is_primary}"
        )
        
        # Load entity details for response
        relationship.entity_details = relationship.entity
        
        return relationship
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating relationship: {str(e)}")

@router.delete("/funds/{fund_id}/entities/{entity_id}", status_code=204)
def delete_fund_entity_relationship(
    fund_id: int,
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlink an entity from a fund"""
    relationship = db.query(FundEntity).filter(
        FundEntity.fund_id == fund_id,
        FundEntity.entity_id == entity_id
    ).first()
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Fund-entity relationship not found")
    
    try:
        # Get user_id for audit logging
        user_id = None
        if "sub" in current_user:
            user = db.query(User).filter(User.email == current_user["sub"]).first()
            if user:
                user_id = user.user_id
        
        # Log activity before deletion
        log_activity(
            db=db,
            user_id=user_id,
            activity="Fund-Entity Unlinked",
            details=f"Unlinked entity from fund"
        )
        
        db.delete(relationship)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting relationship: {str(e)}")

@router.delete("/{fund_entity_id}", status_code=204)
def delete_fund_entity_by_id(
    fund_entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a fund-entity relationship by ID"""
    relationship = db.query(FundEntity).filter(FundEntity.fund_entity_id == fund_entity_id).first()
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Fund-entity relationship not found")
    
    try:
        # Get user_id for audit logging
        user_id = None
        if "sub" in current_user:
            user = db.query(User).filter(User.email == current_user["sub"]).first()
            if user:
                user_id = user.user_id
        
        # Log activity before deletion
        log_activity(
            db=db,
            user_id=user_id,
            activity="Fund-Entity Deleted",
            details=f"Deleted fund-entity relationship ID: {fund_entity_id}"
        )
        
        db.delete(relationship)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting relationship: {str(e)}") 