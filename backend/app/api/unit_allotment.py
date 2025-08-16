"""
Unit Allotment API endpoints
"""
import logging
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc

from ..database.base import get_db
from ..models.unit_allotment import UnitAllotment
from ..models.lp_details import LPDetails
from ..models.lp_drawdowns import LPDrawdown, DrawdownNotice, DrawdownNoticeStatus
from ..models.fund_details import FundDetails
from ..schemas.unit_allotment import (
    UnitAllotmentGenerateRequest,
    UnitAllotmentGenerateResponse,
    UnitAllotmentResponse,
    UnitAllotmentListResponse,
    UnitAllotmentFilter
)
from ..services.unit_calculator import UnitCalculationEngine
from ..services.unit_allotment_excel_generator import UnitAllotmentExcelGenerator
from ..utils.audit import log_activity
from ..utils.s3_storage import S3DocumentStorage, extract_s3_key_from_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unit-allotments", tags=["Unit Allotment"])

@router.post("/generate", response_model=UnitAllotmentGenerateResponse)
async def generate_unit_allotments(
    request: UnitAllotmentGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate unit allotments for all LPs in a fund based on completed payments.
    Only fund_id is required - drawdown_quarter and date_of_allotment are calculated automatically.
    """
    try:
        # Validate fund exists
        fund = db.query(FundDetails).filter(FundDetails.fund_id == request.fund_id).first()
        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fund with ID {request.fund_id} not found"
            )
        
        # Get current date for calculations
        current_date = date.today()
        
        # Initialize services
        calculator = UnitCalculationEngine()
        excel_generator = UnitAllotmentExcelGenerator()
        
        # Calculate drawdown quarter from current date
        drawdown_quarter = calculator.calculate_drawdown_quarter(current_date)
        
        # Find all LPs with paid drawdowns for this fund
        paid_drawdowns = db.query(LPDrawdown).options(
            joinedload(LPDrawdown.lp),
            joinedload(LPDrawdown.fund)
        ).filter(
            and_(
                LPDrawdown.fund_id == request.fund_id,
                LPDrawdown.status != DrawdownNoticeStatus.DRAWDOWN_PAYMENT_PENDING.value,  # Not payment pending = paid
            )
        ).all()
        
        if not paid_drawdowns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No paid drawdowns found for fund {request.fund_id}. Unit allotment requires completed payments."
            )
        
        # Check if allotments already exist (unless force recalculation)
        if not request.force_recalculation:
            existing_allotments = db.query(UnitAllotment).filter(
                and_(
                    UnitAllotment.fund_id == request.fund_id,
                    UnitAllotment.drawdown_quarter == drawdown_quarter
                )
            ).first()
            
            if existing_allotments:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Unit allotments already exist for fund {request.fund_id} quarter {drawdown_quarter}. Use force_recalculation=true to regenerate."
                )
        else:
            # For force recalculation, clean up all existing allotments for this fund/quarter
            existing_allotments = db.query(UnitAllotment).filter(
                and_(
                    UnitAllotment.fund_id == request.fund_id,
                    UnitAllotment.drawdown_quarter == drawdown_quarter
                )
            ).all()
            
            if existing_allotments:
                s3_storage = S3DocumentStorage()
                deleted_files = 0
                
                # Delete all Excel files from S3 for this quarter
                for allotment in existing_allotments:
                    if allotment.excel_file_url:
                        try:
                            # Extract S3 key from URL
                            s3_key = extract_s3_key_from_url(allotment.excel_file_url, s3_storage.bucket_name, s3_storage.region_name)
                            s3_storage.delete_object(s3_key)
                            deleted_files += 1
                        except Exception as e:
                            logger.warning(f"Could not delete Excel file from S3: {e}")
                
                # Delete all database records for this quarter
                db.query(UnitAllotment).filter(
                    and_(
                        UnitAllotment.fund_id == request.fund_id,
                        UnitAllotment.drawdown_quarter == drawdown_quarter
                    )
                ).delete()
                
                logger.info(f"Force recalculation: Deleted {len(existing_allotments)} allotments and {deleted_files} Excel files for quarter {drawdown_quarter}")
        
        # Generate allotments for each paid drawdown
        allotments_created = []
        total_units_allocated = 0
        total_amount_allocated = Decimal('0')
        
        for drawdown in paid_drawdowns:
            try:
                # Calculate all values for this drawdown
                calculations = calculator.calculate_all_for_drawdown(
                    drawdown_amount=drawdown.drawdown_amount,
                    nav_value=fund.nav,
                    commitment_amount=drawdown.lp.commitment_amount,
                    mgmt_fee_rate=fund.mgmt_fee_rate,
                    stamp_duty_rate=fund.stamp_duty_rate,
                    drawdown_date=drawdown.drawdown_due_date
                )
                
                # Note: For force recalculation, cleanup is already handled at quarter level above
                
                # Create new allotment record
                allotment = UnitAllotment(
                    drawdown_id=drawdown.drawdown_id,
                    lp_id=drawdown.lp_id,
                    fund_id=request.fund_id,
                    # LP Information from database
                    first_holder_name=drawdown.lp.lp_name,
                    first_holder_pan=drawdown.lp.pan,
                    clid=drawdown.lp.client_id,
                    dpid=drawdown.lp.dpid,
                    # Calculated values
                    mgmt_fees=calculations['mgmt_fees'],
                    committed_amt=calculations['committed_amt'],
                    amt_accepted=calculations['amt_accepted'],
                    drawdown_amount=calculations['drawdown_amount'],
                    drawdown_date=drawdown.drawdown_due_date,
                    drawdown_quarter=calculations['drawdown_quarter'],
                    nav_value=calculations['nav_value'],
                    allotted_units=calculations['allotted_units'],
                    stamp_duty=calculations['stamp_duty'],
                    date_of_allotment=current_date,
                    status="Generated"
                )
                
                db.add(allotment)
                allotments_created.append(allotment)
                total_units_allocated += calculations['allotted_units']
                total_amount_allocated += calculations['drawdown_amount']
                
            except Exception as e:
                logger.error(f"Error calculating allotment for LP {drawdown.lp.lp_name}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error calculating allotment for LP {drawdown.lp.lp_name}: {str(e)}"
                )
        
        # Commit allotments to database
        db.commit()
        
        # Update all related DrawdownNotice statuses to ALLOTMENT_PENDING
        drawdown_ids = [drawdown.drawdown_id for drawdown in paid_drawdowns]
        db.query(DrawdownNotice).filter(
            DrawdownNotice.drawdown_id.in_(drawdown_ids)
        ).update(
            {DrawdownNotice.status: DrawdownNoticeStatus.ALLOTMENT_PENDING.value},
            synchronize_session=False
        )
        db.commit()
        
        # Refresh objects to get IDs
        for allotment in allotments_created:
            db.refresh(allotment)
        
        # Generate Excel sheet
        try:
            excel_url = excel_generator.generate_allotment_sheet(
                allotments=allotments_created,
                fund_name=fund.scheme_name,
                drawdown_quarter=drawdown_quarter
            )
            
            # Update allotments with Excel file URL
            for allotment in allotments_created:
                allotment.excel_file_url = excel_url
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error generating Excel sheet: {e}")
            # Don't fail the whole operation if Excel generation fails
            excel_url = None
            
            # Update status to ALLOTMENT_SHEET_GENERATION_PENDING if Excel generation failed
            db.query(DrawdownNotice).filter(
                DrawdownNotice.drawdown_id.in_(drawdown_ids)
            ).update(
                {DrawdownNotice.status: DrawdownNoticeStatus.ALLOTMENT_SHEET_GENERATION_PENDING.value},
                synchronize_session=False
            )
            db.commit()
        
        # Log audit activity
        final_status = "Allotment Pending" if excel_url else "Allotment Sheet Generation Pending"
        log_activity(
            db=db,
            activity=f"Unit allotments generated for fund {fund.scheme_name}",
            details=f"Generated {len(allotments_created)} allotments for quarter {drawdown_quarter}, total units: {total_units_allocated}. DrawdownNotice status: {final_status} for all related LPs."
        )
        
        # Convert to response models
        allotment_responses = [
            UnitAllotmentResponse.model_validate(allotment) for allotment in allotments_created
        ]
        
        return UnitAllotmentGenerateResponse(
            success=True,
            message=f"Successfully generated {len(allotments_created)} unit allotments for quarter {drawdown_quarter}",
            allotments=allotment_responses,
            excel_file_url=excel_url,
            total_lps=len(allotments_created),
            total_units_allocated=total_units_allocated,
            total_amount_allocated=total_amount_allocated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in unit allotment generation: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during unit allotment generation: {str(e)}"
        )

@router.get("", response_model=UnitAllotmentListResponse)
async def list_unit_allotments(
    fund_id: Optional[int] = Query(None, description="Filter by fund ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    drawdown_quarter: Optional[str] = Query(None, description="Filter by drawdown quarter"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List unit allotments with optional filtering and pagination.
    """
    try:
        # Build query with filters
        query = db.query(UnitAllotment).options(
            joinedload(UnitAllotment.lp),
            joinedload(UnitAllotment.fund),
            joinedload(UnitAllotment.drawdown)
        )
        
        if fund_id:
            query = query.filter(UnitAllotment.fund_id == fund_id)
        
        if status:
            query = query.filter(UnitAllotment.status == status)
        
        if drawdown_quarter:
            query = query.filter(UnitAllotment.drawdown_quarter == drawdown_quarter)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        allotments = query.order_by(desc(UnitAllotment.created_at)).offset(skip).limit(limit).all()
        
        # Convert to response models
        allotment_responses = [
            UnitAllotmentResponse.model_validate(allotment) for allotment in allotments
        ]
        
        return UnitAllotmentListResponse(
            allotments=allotment_responses,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing unit allotments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving unit allotments: {str(e)}"
        )

@router.get("/{allotment_id}", response_model=UnitAllotmentResponse)
async def get_unit_allotment(
    allotment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific unit allotment details by ID.
    """
    try:
        allotment = db.query(UnitAllotment).options(
            joinedload(UnitAllotment.lp),
            joinedload(UnitAllotment.fund),
            joinedload(UnitAllotment.drawdown)
        ).filter(UnitAllotment.allotment_id == allotment_id).first()
        
        if not allotment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unit allotment with ID {allotment_id} not found"
            )
        
        return UnitAllotmentResponse.model_validate(allotment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving unit allotment {allotment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving unit allotment: {str(e)}"
        )

@router.get("/{allotment_id}/excel")
async def get_allotment_excel(
    allotment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the Excel file URL for a specific unit allotment.
    """
    try:
        allotment = db.query(UnitAllotment).filter(
            UnitAllotment.allotment_id == allotment_id
        ).first()
        
        if not allotment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unit allotment with ID {allotment_id} not found"
            )
        
        if not allotment.excel_file_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Excel file not available for allotment {allotment_id}"
            )
        
        return {
            "allotment_id": allotment_id,
            "excel_file_url": allotment.excel_file_url,
            "status": allotment.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Excel file for allotment {allotment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving Excel file: {str(e)}"
        )

@router.delete("/{allotment_id}")
async def delete_unit_allotment(
    allotment_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a unit allotment record and its associated Excel file from S3.
    """
    try:
        # Find the allotment
        allotment = db.query(UnitAllotment).filter(
            UnitAllotment.allotment_id == allotment_id
        ).first()
        
        if not allotment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unit allotment with ID {allotment_id} not found"
            )
        
        # Store details for audit log
        lp_name = allotment.first_holder_name
        excel_url = allotment.excel_file_url
        
        # Delete Excel file from S3 if exists
        if excel_url:
            try:
                s3_storage = S3DocumentStorage()
                # Extract S3 key from URL
                s3_key = extract_s3_key_from_url(excel_url, s3_storage.bucket_name, s3_storage.region_name)
                s3_storage.delete_object(s3_key)
                logger.info(f"Deleted Excel file from S3: {excel_url}")
            except Exception as e:
                logger.warning(f"Could not delete Excel file from S3: {e}")
        
        # Delete from database
        db.delete(allotment)
        db.commit()
        
        # Log audit activity
        log_activity(
            db=db,
            activity=f"Unit allotment deleted for {lp_name}",
            details=f"Allotment ID {allotment_id} deleted, Excel file removed from S3"
        )
        
        return {
            "success": True,
            "message": f"Unit allotment {allotment_id} deleted successfully",
            "deleted_allotment_id": allotment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting unit allotment {allotment_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting unit allotment: {str(e)}"
        )

