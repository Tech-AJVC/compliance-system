from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..database.base import get_db
from ..models.entity import Entity
from ..models.user import User
from ..schemas.entity import EntityCreate, EntityUpdate, EntityResponse, EntitySearch, EntityType
from ..utils.audit import log_activity
from ..auth.security import get_current_user

router = APIRouter(prefix="/entities", tags=["entities"])

@router.post("/", response_model=EntityResponse, status_code=201)
def create_entity(
    entity_data: EntityCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new entity"""
    try:
        # Create new entity
        db_entity = Entity(**entity_data.model_dump())
        db.add(db_entity)
        db.commit()
        db.refresh(db_entity)
        
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
            activity="Entity Created",
            details=f"Created entity: {db_entity.entity_type} - {db_entity.entity_pan}"
        )
        
        return db_entity
        
    except Exception as e:
        db.rollback()
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Entity with this PAN already exists")
        raise HTTPException(status_code=400, detail=f"Error creating entity: {str(e)}")

@router.get("/", response_model=List[EntityResponse])
def list_entities(
    entity_type: Optional[EntityType] = Query(None, description="Filter by entity type"),
    gst_number: Optional[str] = Query(None, description="Filter by GST number"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List entities with optional filtering"""
    query = db.query(Entity)
    
    if entity_type:
        query = query.filter(Entity.entity_type == entity_type.value)
    
    if gst_number:
        query = query.filter(Entity.entity_gst_number == gst_number)
    
    entities = query.offset(skip).limit(limit).all()
    return entities

@router.get("/search", response_model=List[EntitySearch])
def search_entities(
    query: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search entities by name or POC with pagination"""
    entities = db.query(Entity).filter(
        or_(
            Entity.entity_name.ilike(f"%{query}%"),
            Entity.entity_poc.ilike(f"%{query}%")
        )
    ).offset(skip).limit(limit).all()
    
    return [
        EntitySearch(
            entity_id=entity.entity_id,
            entity_name=entity.entity_name or "—",
            entity_type=entity.entity_type
        )
        for entity in entities
    ]

@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity(
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific entity by ID"""
    entity = db.query(Entity).filter(Entity.entity_id == entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity

@router.put("/{entity_id}", response_model=EntityResponse)
def update_entity(
    entity_id: int,
    entity_data: EntityUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing entity"""
    entity = db.query(Entity).filter(Entity.entity_id == entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    try:
        # Update entity with provided data (partial update allowed)
        update_data = entity_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entity, field, value)
        
        db.commit()
        db.refresh(entity)
        
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
            activity="Entity Updated",
            details=f"Updated entity: {entity.entity_type} - {entity.entity_pan}"
        )
        
        return entity
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating entity: {str(e)}")

@router.delete("/{entity_id}", status_code=204)
def delete_entity(
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an entity"""
    entity = db.query(Entity).filter(Entity.entity_id == entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
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
            activity="Entity Deleted",
            details=f"Deleted entity: {entity.entity_type} - {entity.entity_pan}"
        )
        
        db.delete(entity)
        db.commit()
        
    except Exception as e:
        db.rollback()
        if "foreign key" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete entity: it is linked to one or more funds"
            )
        raise HTTPException(status_code=400, detail=f"Error deleting entity: {str(e)}") 