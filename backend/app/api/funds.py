from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from ..database.base import get_db
from ..models.fund_details import FundDetails
from ..models.fund_entity import FundEntity
from ..models.entity import Entity
from ..models.user import User
from ..schemas.fund import (
    FundCreate, FundUpdate, FundResponse, FundSearch, FundDetailsSummary
)
from ..utils.audit import log_activity
from ..auth.security import get_current_user

router = APIRouter(prefix="/funds", tags=["funds"])

def validate_fund_uniqueness(db: Session, fund_data: FundCreate) -> Optional[Dict[str, Any]]:
    """
    Validate that fund fields are unique before creation.
    Returns error dict if validation fails, None if all validations pass.
    """
    # Check scheme_name
    if fund_data.scheme_name:
        existing_fund = db.query(FundDetails).filter(
            FundDetails.scheme_name == fund_data.scheme_name
        ).first()
        if existing_fund:
            return {
                "error_type": "validation_error",
                "field": "scheme_name",
                "value": fund_data.scheme_name,
                "message": f"A fund with scheme name '{fund_data.scheme_name}' already exists"
            }
    
    # Check aif_pan
    if fund_data.aif_pan:
        existing_fund = db.query(FundDetails).filter(
            FundDetails.aif_pan == fund_data.aif_pan
        ).first()
        if existing_fund:
            return {
                "error_type": "validation_error",
                "field": "aif_pan",
                "value": fund_data.aif_pan,
                "message": f"A fund with AIF PAN '{fund_data.aif_pan}' already exists"
            }
    
    # Check bank_account_no
    if fund_data.bank_account_no:
        existing_fund = db.query(FundDetails).filter(
            FundDetails.bank_account_no == fund_data.bank_account_no
        ).first()
        if existing_fund:
            return {
                "error_type": "validation_error",
                "field": "bank_account_no",
                "value": fund_data.bank_account_no,
                "message": f"A fund with bank account number '{fund_data.bank_account_no}' already exists"
            }
    
    return None

@router.post("/", response_model=FundResponse, status_code=201)
def create_fund(
    fund_data: FundCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new fund"""
    try:
        # Validate fund uniqueness before creation
        validation_error = validate_fund_uniqueness(db, fund_data)
        if validation_error:
            raise HTTPException(status_code=400, detail=validation_error)
        
        # Create new fund
        db_fund = FundDetails(**fund_data.model_dump())
        db.add(db_fund)
        db.commit()
        db.refresh(db_fund)
        
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
            activity="Fund Created",
            details=f"Created fund: {db_fund.scheme_name}"
        )
        
        return db_fund
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating fund: {str(e)}")

@router.get("/", response_model=List[FundResponse])
def list_funds(
    scheme_status: Optional[str] = Query(None, description="Filter by scheme status"),
    legal_structure: Optional[str] = Query(None, description="Filter by legal structure"),
    category_subcategory: Optional[str] = Query(None, description="Filter by category subcategory"),
    scheme_structure_type: Optional[str] = Query(None, description="Filter by scheme structure type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List funds with optional filtering"""
    query = db.query(FundDetails)
    
    if scheme_status:
        query = query.filter(FundDetails.scheme_status == scheme_status)
    
    if legal_structure:
        query = query.filter(FundDetails.legal_structure == legal_structure)
    
    if category_subcategory:
        query = query.filter(FundDetails.category_subcategory == category_subcategory)
    
    if scheme_structure_type:
        query = query.filter(FundDetails.scheme_structure_type == scheme_structure_type)
    
    funds = query.offset(skip).limit(limit).all()
    return funds

@router.get("/search", response_model=List[FundSearch])
def search_funds(
    query: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search funds by scheme name or AIF name with pagination"""
    funds = db.query(FundDetails).filter(
        or_(
            FundDetails.scheme_name.ilike(f"%{query}%"),
            FundDetails.aif_name.ilike(f"%{query}%")
        )
    ).offset(skip).limit(limit).all()
    
    return [
        FundSearch(
            fund_id=fund.fund_id,
            scheme_name=fund.scheme_name
        )
        for fund in funds
    ]

@router.get("/{fund_id}", response_model=FundResponse)
def get_fund(
    fund_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific fund by ID"""
    fund = db.query(FundDetails).filter(FundDetails.fund_id == fund_id).first()
    
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    return fund

@router.get("/{fund_id}/details-summary", response_model=FundDetailsSummary)
def get_fund_details_summary(
    fund_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive fund information for reporting"""
    fund = db.query(FundDetails).filter(FundDetails.fund_id == fund_id).first()
    
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    # Build comprehensive summary based on the image provided
    summary = FundDetailsSummary(
        fund_id=fund.fund_id,
        scheme_details={
            "name": fund.scheme_name,
            "status": fund.scheme_status,
            "pan": fund.scheme_pan,
            "date_of_filing_final_draft_ppm_with_sebi": fund.date_final_draft_ppm.isoformat() if fund.date_final_draft_ppm else None,
            "date_of_sebi_communication_for_taking_ppm_on_record": fund.date_sebi_ppm_comm.isoformat() if fund.date_sebi_ppm_comm else None,
            "date_of_launch_of_scheme": fund.date_launch_of_scheme.isoformat() if fund.date_launch_of_scheme else None,
            "date_of_initial_close": fund.date_initial_close.isoformat() if fund.date_initial_close else None,
            "date_of_final_close": fund.date_final_close.isoformat() if fund.date_final_close else None,
            "total_commitment_received_corpus_initial_close_rs_cr": float(fund.commitment_initial_close_cr) if fund.commitment_initial_close_cr else None,
            "target_fund_size": float(fund.target_fund_size) if fund.target_fund_size else None,
            "greenshoe_option": float(fund.greenshoe_option) if fund.greenshoe_option else None,
            "end_date_of_terms_of_scheme": fund.terms_end_date.isoformat() if fund.terms_end_date else None,
            "extension_of_term_permitted_as_per_fund_documents": "Yes" if fund.extension_permitted else "No" if fund.extension_permitted is not None else None
        },
        aif_details={
            "name": fund.aif_name,
            "pan": fund.aif_pan,
            "registration_number": fund.aif_registration_no,
            "legal_structure": fund.legal_structure,
            "category_and_subcategory": fund.category_subcategory
        },
        financial_info={
            "corpus_initial_close": float(fund.commitment_initial_close_cr) if fund.commitment_initial_close_cr else None,
            "target_fund_size": float(fund.target_fund_size) if fund.target_fund_size else None,
            "greenshoe_option": float(fund.greenshoe_option) if fund.greenshoe_option else None
        },
        important_dates={
            "ppm_final_draft_sent": fund.date_final_draft_ppm.isoformat() if fund.date_final_draft_ppm else None,
            "ppm_taken_on_record": fund.date_sebi_ppm_comm.isoformat() if fund.date_sebi_ppm_comm else None,
            "scheme_launch": fund.date_launch_of_scheme.isoformat() if fund.date_launch_of_scheme else None,
            "initial_close": fund.date_initial_close.isoformat() if fund.date_initial_close else None,
            "final_close": fund.date_final_close.isoformat() if fund.date_final_close else None,
            "end_date_scheme": fund.terms_end_date.isoformat() if fund.terms_end_date else None,
            "end_date_extended": fund.extended_end_date.isoformat() if fund.extended_end_date else None
        },
        bank_details={
            "name": fund.bank_name,
            "ifsc": fund.bank_ifsc,
            "bank_account_name": fund.bank_account_name,
            "bank_account_number": fund.bank_account_no,
            "bank_contact": fund.bank_contact_person,
            "contact_phone": fund.bank_contact_phone
        }
    )
    
    return summary

@router.put("/{fund_id}", response_model=FundResponse)
def update_fund(
    fund_id: int,
    fund_data: FundUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing fund"""
    fund = db.query(FundDetails).filter(FundDetails.fund_id == fund_id).first()
    
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    try:
        # Update fund with provided data (partial update allowed)
        update_data = fund_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(fund, field, value)
        
        db.commit()
        db.refresh(fund)
        
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
            activity="Fund Updated",
            details=f"Updated fund: {fund.scheme_name}"
        )
        
        return fund
        
    except Exception as e:
        db.rollback()
        if "duplicate key" in str(e).lower():
            if "scheme_name" in str(e):
                raise HTTPException(status_code=400, detail="Fund with this scheme name already exists")
            elif "aif_pan" in str(e):
                raise HTTPException(status_code=400, detail="Fund with this AIF PAN already exists")
            elif "bank_account_no" in str(e):
                raise HTTPException(status_code=400, detail="Fund with this bank account number already exists")
        raise HTTPException(status_code=400, detail=f"Error updating fund: {str(e)}")

@router.delete("/{fund_id}", status_code=204)
def delete_fund(
    fund_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a fund"""
    fund = db.query(FundDetails).filter(FundDetails.fund_id == fund_id).first()
    
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
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
            activity="Fund Deleted",
            details=f"Deleted fund: {fund.scheme_name}"
        )
        
        db.delete(fund)
        db.commit()
        
    except Exception as e:
        db.rollback()
        if "foreign key" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete fund: it has associated LP details or drawdowns"
            )
        raise HTTPException(status_code=400, detail=f"Error deleting fund: {str(e)}") 