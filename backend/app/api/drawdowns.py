"""
Drawdown API endpoints for capital call management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, asc
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime
import logging
import uuid

from ..database.base import get_db
from ..auth.security import get_current_user
from ..models import LPDrawdown, DrawdownNotice, LPDetails, FundDetails, Document, LPPayment
from ..models.lp_drawdowns import DrawdownNoticeStatus
from ..schemas.drawdown import (
    DrawdownGenerateRequest, DrawdownGenerateResponse,
    DrawdownPreviewRequest, DrawdownPreviewResponse, LPDrawdownPreview,
    DrawdownStatusUpdateRequest, DrawdownUpdateRequest, LPDrawdownResponse, DrawdownNoticeResponse,
    DrawdownWithBankDetails, DrawdownListResponse, DrawdownSummaryResponse
)
from ..utils.capital_call_generator.capital_call_html_generator import generate_capital_call_pdf, CapitalCallHTMLGenerator
from ..utils.s3_storage import get_s3_storage

router = APIRouter()
logger = logging.getLogger(__name__)

def calculate_quarter_string(notice_date: date) -> str:
    """Calculate quarter string from notice date"""
    # Fiscal year quarters: Q1 (Apr-Jun), Q2 (Jul-Sep), Q3 (Oct-Dec), Q4 (Jan-Mar)
    quarter_map = {1: "Q4", 2: "Q4", 3: "Q4", 4: "Q1", 5: "Q1", 6: "Q1",
                   7: "Q2", 8: "Q2", 9: "Q2", 10: "Q3", 11: "Q3", 12: "Q3"}
    quarter = quarter_map[notice_date.month]
    year_short = str(notice_date.year)[2:]
    return f"{quarter}'{year_short}"

def calculate_next_quarter_period(current_quarter: str) -> str:
    """Auto-calculate next quarter period from current quarter"""
    # Parse current quarter (e.g., "Q1'25")
    quarter_num = int(current_quarter[1])
    year = current_quarter[3:]
    
    # Calculate next quarter
    if quarter_num == 4:
        next_quarter = "Q1"
        next_year = str(int(year) + 1).zfill(2)
    else:
        next_quarter = f"Q{quarter_num + 1}"
        next_year = year
    
    return f"{next_quarter}'{next_year}"

def calculate_drawdown_amounts(lp: LPDetails, percentage: Decimal, db: Session) -> dict:
    """Calculate drawdown amounts for a specific LP"""
    committed_amt = lp.commitment_amount or Decimal('0')
    drawdown_amount = (percentage / 100) * committed_amt
    
    # Calculate amount called up (sum of previous drawdowns)
    previous_drawdowns = db.query(func.sum(LPDrawdown.drawdown_amount)).filter(
        and_(LPDrawdown.lp_id == lp.lp_id, LPDrawdown.status != 'Cancelled')
    ).scalar() or Decimal('0')
    
    amount_called_up = previous_drawdowns + drawdown_amount
    remaining_commitment = committed_amt - amount_called_up
    
    return {
        'committed_amt': committed_amt,
        'drawdown_amount': drawdown_amount,
        'amount_called_up': amount_called_up,
        'remaining_commitment': remaining_commitment
    }

@router.post("/generate_drawdowns", response_model=DrawdownGenerateResponse)
def generate_drawdowns(
    request: DrawdownGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate drawdown notices for all LPs in a fund
    
    This endpoint:
    1. Validates the fund exists
    2. Gets all LPs for the fund
    3. Calculates drawdown amounts for each LP
    4. Creates LPDrawdown and DrawdownNotice records
    5. Generates PDF notices using capital_call_html_generator
    6. Returns list of generated PDFs and drawdown details
    """
    try:
        # Validate fund exists
        fund = db.query(FundDetails).filter(FundDetails.fund_id == request.fund_id).first()
        if not fund:
            raise HTTPException(status_code=404, detail=f"Fund with ID {request.fund_id} not found")
        
        # Get all LPs for this fund
        lps = db.query(LPDetails).filter(
            and_(LPDetails.fund_id == request.fund_id, LPDetails.status == "Active")
        ).all()
        
        if not lps:
            raise HTTPException(status_code=404, detail=f"No verified LPs found for fund {request.fund_id}")
        
        # Calculate quarter string and next quarter period
        drawdown_quarter = calculate_quarter_string(request.notice_date)
        forecast_next_quarter_period = calculate_next_quarter_period(drawdown_quarter)
        
        # Check if drawdown already exists for this quarter
        existing_drawdown = db.query(LPDrawdown).filter(
            and_(
                LPDrawdown.fund_id == request.fund_id,
                LPDrawdown.drawdown_quarter == drawdown_quarter
            )
        ).first()
        
        if existing_drawdown:
            raise HTTPException(
                status_code=400, 
                detail=f"Drawdown already generated for fund {request.fund_id} in quarter {drawdown_quarter}"
            )
        
        created_drawdowns = []
        generated_pdfs = []
        total_amount = Decimal('0')
        
        for lp in lps:
            # Calculate amounts for this LP
            amounts = calculate_drawdown_amounts(lp, request.percentage_drawdown, db)
            
            # Create LPDrawdown record
            drawdown = LPDrawdown(
                fund_id=request.fund_id,
                lp_id=lp.lp_id,
                notice_date=request.notice_date,
                drawdown_due_date=request.due_date,
                drawdown_percentage=request.percentage_drawdown,
                drawdown_quarter=drawdown_quarter,
                committed_amt=amounts['committed_amt'],
                drawdown_amount=amounts['drawdown_amount'],
                amount_called_up=amounts['amount_called_up'],
                remaining_commitment=amounts['remaining_commitment'],
                forecast_next_quarter=request.forecast_next_quarter,
                forecast_next_quarter_period=forecast_next_quarter_period,
                status=DrawdownNoticeStatus.DRAWDOWN_PAYMENT_PENDING.value
            )
            
            db.add(drawdown)
            db.flush()  # Flush to get the drawdown_id
            
            # Prepare data for PDF generation
            pdf_data = {
                'notice_date': request.notice_date.strftime('%Y-%m-%d'),
                'investor': lp.lp_name,
                'amount_due': float(amounts['drawdown_amount']),
                'total_commitment': float(amounts['committed_amt']),
                'amount_called_up': float(amounts['amount_called_up']),
                'remaining_commitment': float(amounts['remaining_commitment']),
                'contribution_due_date': request.due_date.strftime('%Y-%m-%d'),
                'bank_name': fund.bank_name,
                'ifsc': fund.bank_ifsc,
                'acct_name': fund.bank_account_name,
                'acct_number': fund.bank_account_no,
                'bank_contact': fund.bank_contact_person,
                'phone': fund.bank_contact_phone,
                'forecast_next_quarter': float(request.forecast_next_quarter),
                'forecast_next_quarter_period': forecast_next_quarter_period
            }
            
            # Generate PDF
            try:
                pdf_path = generate_capital_call_pdf(pdf_data)
                
                # Upload PDF to S3
                s3_url = None
                s3_key = None
                try:
                    s3_storage = get_s3_storage()
                    
                    # Create folder structure: Fund Scheme/Quarter/Capital Calls/
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_lp_name = "".join(c for c in lp.lp_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_lp_name = safe_lp_name.replace(' ', '_')
                    safe_fund_name = "".join(c for c in fund.scheme_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_fund_name = safe_fund_name.replace(' ', '_')
                    
                    # S3 key: FundScheme/Quarter/Capital Calls/lp_name_timestamp.pdf
                    s3_key = f"{safe_fund_name}/{drawdown_quarter}/Capital Calls/{safe_lp_name}_{timestamp}.pdf"
                    
                    # Prepare metadata
                    metadata = {
                        'document_type': 'capital_call',
                        'quarter': drawdown_quarter,
                        'lp_name': lp.lp_name,
                        'fund_name': fund.scheme_name,
                        'fund_id': str(request.fund_id),
                        'drawdown_id': str(drawdown.drawdown_id),
                        'drawdown_percentage': str(request.percentage_drawdown),
                        'notice_date': request.notice_date.isoformat(),
                        'due_date': request.due_date.isoformat(),
                        'generated_timestamp': timestamp
                    }
                    
                    upload_result = s3_storage.upload_file(
                        local_file_path=pdf_path,
                        s3_key=s3_key,
                        metadata=metadata,
                        content_type='application/pdf'
                    )
                    
                    if upload_result['success']:
                        s3_url = upload_result['s3_url']
                        logger.info(f"Successfully uploaded PDF for {lp.lp_name} to S3: {s3_key}")
                        generated_pdfs.append(s3_url)
                        # Clean up local file after successful S3 upload
                        try:
                            import os
                            if os.path.exists(pdf_path):
                                os.remove(pdf_path)
                                logger.info(f"Cleaned up local PDF file: {pdf_path}")
                        except Exception as cleanup_error:
                            logger.warning(f"Failed to clean up local PDF file {pdf_path}: {str(cleanup_error)}")
                    else:
                        logger.warning(f"Failed to upload PDF for {lp.lp_name} to S3: {upload_result.get('error', 'Unknown error')}")
                        
                except Exception as s3_error:
                    logger.warning(f"S3 upload failed for {lp.lp_name}: {str(s3_error)}. PDF saved locally only.")
                
                # Create DrawdownNotice record
                notice = DrawdownNotice(
                    drawdown_id=drawdown.drawdown_id,
                    lp_id=lp.lp_id,
                    notice_date=request.notice_date,
                    amount_due=amounts['drawdown_amount'],
                    due_date=request.due_date,
                    pdf_file_path=s3_url or pdf_path,  # Use S3 URL if available, otherwise local path
                    status=DrawdownNoticeStatus.DRAWDOWN_PAYMENT_PENDING.value
                )
                
                db.add(notice)
                
            except Exception as e:
                logger.error(f"Failed to generate PDF for LP {lp.lp_name}: {str(e)}")
                # Continue with other LPs even if one PDF generation fails
                notice = DrawdownNotice(
                    drawdown_id=drawdown.drawdown_id,
                    lp_id=lp.lp_id,
                    notice_date=request.notice_date,
                    amount_due=amounts['drawdown_amount'],
                    due_date=request.due_date,
                    status=DrawdownNoticeStatus.DRAWDOWN_PAYMENT_PENDING.value  # Still set to pending even if PDF failed
                )
                db.add(notice)
            
            created_drawdowns.append(drawdown)
            total_amount += amounts['drawdown_amount']
        
        # Commit all changes
        db.commit()
        
        # Refresh all objects to get the latest data
        for drawdown in created_drawdowns:
            db.refresh(drawdown)
        
        logger.info(f"Generated {len(created_drawdowns)} drawdowns for fund {request.fund_id}, quarter {drawdown_quarter}")
        
        return DrawdownGenerateResponse(
            success=True,
            message=f"Successfully generated {len(created_drawdowns)} drawdown notices",
            drawdown_count=len(created_drawdowns),
            fund_id=request.fund_id,
            drawdown_quarter=drawdown_quarter,
            total_amount=total_amount,
            generated_pdfs=generated_pdfs,
            drawdowns=[LPDrawdownResponse.model_validate(d) for d in created_drawdowns]
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error generating drawdowns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating drawdowns: {str(e)}")

@router.post("/preview", response_model=DrawdownPreviewResponse)
def preview_drawdowns(
    request: DrawdownPreviewRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview drawdown calculations without persisting to database
    """
    try:
        # Validate fund exists
        fund = db.query(FundDetails).filter(FundDetails.fund_id == request.fund_id).first()
        if not fund:
            raise HTTPException(status_code=404, detail=f"Fund with ID {request.fund_id} not found")
        
        # Get all LPs for this fund
        lps = db.query(LPDetails).filter(
            and_(LPDetails.fund_id == request.fund_id, LPDetails.status == "Active")
        ).all()
        
        if not lps:
            raise HTTPException(status_code=404, detail=f"No verified LPs found for fund {request.fund_id}")
        
        lp_previews = []
        total_amount = Decimal('0')
        
        for lp in lps:
            amounts = calculate_drawdown_amounts(lp, request.percentage_drawdown, db)
            
            preview = LPDrawdownPreview(
                lp_id=lp.lp_id,
                lp_name=lp.lp_name,
                commitment_amount=amounts['committed_amt'],
                drawdown_amount=amounts['drawdown_amount'],
                amount_called_up=amounts['amount_called_up'],
                remaining_commitment=amounts['remaining_commitment']
            )
            
            lp_previews.append(preview)
            total_amount += amounts['drawdown_amount']
        
        preview_id = f"temp_{uuid.uuid4()}"
        
        summary = {
            "total_lps": len(lps),
            "total_amount": float(total_amount),
            "average_drawdown": float(total_amount / len(lps)) if lps else 0
        }
        
        # Generate HTML preview for the first LP
        sample_html_preview = None
        if lps and lp_previews:
            try:
                # Calculate quarter string and next quarter period
                drawdown_quarter = calculate_quarter_string(request.notice_date)
                forecast_next_quarter_period = calculate_next_quarter_period(drawdown_quarter)
                
                # Get first LP and its amounts
                first_lp = lps[0]
                first_amounts = calculate_drawdown_amounts(first_lp, request.percentage_drawdown, db)
                
                # Prepare data for HTML generation (same as in generate_drawdowns)
                html_data = {
                    'notice_date': request.notice_date.strftime('%Y-%m-%d'),
                    'investor': first_lp.lp_name,
                    'amount_due': float(first_amounts['drawdown_amount']),
                    'total_commitment': float(first_amounts['committed_amt']),
                    'amount_called_up': float(first_amounts['amount_called_up']),
                    'remaining_commitment': float(first_amounts['remaining_commitment']),
                    'contribution_due_date': request.due_date.strftime('%Y-%m-%d'),
                    'bank_name': fund.bank_name or "Bank Name Not Set",
                    'ifsc': fund.bank_ifsc or "IFSC Not Set",
                    'acct_name': fund.bank_account_name or "Account Name Not Set",
                    'acct_number': fund.bank_account_no or "Account Number Not Set",
                    'bank_contact': fund.bank_contact_person or "Contact Not Set",
                    'phone': fund.bank_contact_phone or "Phone Not Set",
                    'forecast_next_quarter': float(request.forecast_next_quarter),
                    'forecast_next_quarter_period': forecast_next_quarter_period
                }
                
                # Generate HTML using the HTML generator
                html_generator = CapitalCallHTMLGenerator()
                sample_html_preview = html_generator.generate_html(html_data)
                
            except Exception as e:
                logger.warning(f"Failed to generate HTML preview: {str(e)}")
                sample_html_preview = None
        
        return DrawdownPreviewResponse(
            preview_id=preview_id,
            total_drawdown_amount=total_amount,
            lp_previews=lp_previews,
            summary=summary,
            sample_html_preview=sample_html_preview
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in drawdown preview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")

@router.get("/", response_model=DrawdownListResponse)
def list_drawdowns(
    fund_id: Optional[int] = Query(None, description="Filter by fund ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    quarter: Optional[str] = Query(None, description="Filter by quarter"),
    
    # Range filters for percentage and amounts
    drawdown_percentage_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum drawdown percentage"),
    drawdown_percentage_max: Optional[float] = Query(None, ge=0, le=100, description="Maximum drawdown percentage"),
    committed_amt_min: Optional[float] = Query(None, ge=0, description="Minimum committed amount"),
    committed_amt_max: Optional[float] = Query(None, ge=0, description="Maximum committed amount"),
    amount_called_up_min: Optional[float] = Query(None, ge=0, description="Minimum amount called up"),
    amount_called_up_max: Optional[float] = Query(None, ge=0, description="Maximum amount called up"),
    remaining_commitment_min: Optional[float] = Query(None, ge=0, description="Minimum remaining commitment"),
    remaining_commitment_max: Optional[float] = Query(None, ge=0, description="Maximum remaining commitment"),
    forecast_next_quarter_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum forecast next quarter percentage"),
    forecast_next_quarter_max: Optional[float] = Query(None, ge=0, le=100, description="Maximum forecast next quarter percentage"),
    
    # Date range filters
    notice_date_from: Optional[date] = Query(None, description="Filter notice date from (YYYY-MM-DD)"),
    notice_date_to: Optional[date] = Query(None, description="Filter notice date to (YYYY-MM-DD)"),
    drawdown_due_date_from: Optional[date] = Query(None, description="Filter due date from (YYYY-MM-DD)"),
    drawdown_due_date_to: Optional[date] = Query(None, description="Filter due date to (YYYY-MM-DD)"),
    
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List drawdowns with comprehensive filtering and pagination using skip/limit
    
    Supports filtering by:
    - Basic filters: fund_id, status, quarter
    - Range filters: drawdown_percentage, committed_amt, amount_called_up, remaining_commitment, forecast_next_quarter
    - Date range filters: notice_date, drawdown_due_date
    """
    try:
        query = db.query(LPDrawdown).options(
            joinedload(LPDrawdown.lp),
            joinedload(LPDrawdown.fund)
        )
        
        # Apply basic filters
        if fund_id:
            query = query.filter(LPDrawdown.fund_id == fund_id)
        if status:
            query = query.filter(LPDrawdown.status == status)
        if quarter:
            query = query.filter(LPDrawdown.drawdown_quarter == quarter)
        
        # Apply percentage range filters
        if drawdown_percentage_min is not None:
            query = query.filter(LPDrawdown.drawdown_percentage >= drawdown_percentage_min)
        if drawdown_percentage_max is not None:
            query = query.filter(LPDrawdown.drawdown_percentage <= drawdown_percentage_max)
        
        # Apply amount range filters
        if committed_amt_min is not None:
            query = query.filter(LPDrawdown.committed_amt >= committed_amt_min)
        if committed_amt_max is not None:
            query = query.filter(LPDrawdown.committed_amt <= committed_amt_max)
            
        if amount_called_up_min is not None:
            query = query.filter(LPDrawdown.amount_called_up >= amount_called_up_min)
        if amount_called_up_max is not None:
            query = query.filter(LPDrawdown.amount_called_up <= amount_called_up_max)
            
        if remaining_commitment_min is not None:
            query = query.filter(LPDrawdown.remaining_commitment >= remaining_commitment_min)
        if remaining_commitment_max is not None:
            query = query.filter(LPDrawdown.remaining_commitment <= remaining_commitment_max)
        
        # Apply forecast range filters
        if forecast_next_quarter_min is not None:
            query = query.filter(LPDrawdown.forecast_next_quarter >= forecast_next_quarter_min)
        if forecast_next_quarter_max is not None:
            query = query.filter(LPDrawdown.forecast_next_quarter <= forecast_next_quarter_max)
        
        # Apply date range filters
        if notice_date_from:
            query = query.filter(LPDrawdown.notice_date >= notice_date_from)
        if notice_date_to:
            query = query.filter(LPDrawdown.notice_date <= notice_date_to)
            
        if drawdown_due_date_from:
            query = query.filter(LPDrawdown.drawdown_due_date >= drawdown_due_date_from)
        if drawdown_due_date_to:
            query = query.filter(LPDrawdown.drawdown_due_date <= drawdown_due_date_to)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination using skip/limit
        drawdowns = query.order_by(desc(LPDrawdown.created_at)).offset(skip).limit(limit).all()
        
        # Log filter usage for analytics
        active_filters = []
        if fund_id: active_filters.append("fund_id")
        if status: active_filters.append("status")
        if quarter: active_filters.append("quarter")
        if drawdown_percentage_min is not None or drawdown_percentage_max is not None: active_filters.append("drawdown_percentage_range")
        if committed_amt_min is not None or committed_amt_max is not None: active_filters.append("committed_amt_range")
        if amount_called_up_min is not None or amount_called_up_max is not None: active_filters.append("amount_called_up_range")
        if remaining_commitment_min is not None or remaining_commitment_max is not None: active_filters.append("remaining_commitment_range")
        if forecast_next_quarter_min is not None or forecast_next_quarter_max is not None: active_filters.append("forecast_next_quarter_range")
        if notice_date_from or notice_date_to: active_filters.append("notice_date_range")
        if drawdown_due_date_from or drawdown_due_date_to: active_filters.append("drawdown_due_date_range")
        
        if active_filters:
            logger.info(f"Drawdown list query with filters: {', '.join(active_filters)} - Results: {len(drawdowns)}/{total_count}")
        
        return DrawdownListResponse(
            drawdowns=[LPDrawdownResponse.model_validate(d) for d in drawdowns],
            total_count=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing drawdowns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing drawdowns: {str(e)}")

@router.get("/{drawdown_id}", response_model=LPDrawdownResponse)
def get_drawdown(
    drawdown_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific drawdown details
    """
    try:
        drawdown = db.query(LPDrawdown).options(
            joinedload(LPDrawdown.lp),
            joinedload(LPDrawdown.fund)
        ).filter(LPDrawdown.drawdown_id == drawdown_id).first()
        
        if not drawdown:
            raise HTTPException(status_code=404, detail=f"Drawdown {drawdown_id} not found")
        
        return LPDrawdownResponse.model_validate(drawdown)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drawdown {drawdown_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting drawdown: {str(e)}")

@router.delete("/{drawdown_id}")
def delete_drawdown(
    drawdown_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete drawdown and associated documents from S3 and database
    """
    try:
        # Get the drawdown with related notices
        drawdown = db.query(LPDrawdown).filter(LPDrawdown.drawdown_id == drawdown_id).first()
        
        if not drawdown:
            raise HTTPException(status_code=404, detail=f"Drawdown {drawdown_id} not found")
        
        # Get all associated drawdown notices
        notices = db.query(DrawdownNotice).filter(DrawdownNotice.drawdown_id == drawdown_id).all()
        
        # Delete PDFs from S3 if they exist
        s3_storage = None
        try:
            s3_storage = get_s3_storage()
        except Exception as e:
            logger.warning(f"S3 not configured, skipping S3 cleanup: {str(e)}")
        
        deleted_files = []
        failed_deletions = []
        
        for notice in notices:
            if notice.pdf_file_path and s3_storage:
                try:
                    # Extract S3 key from URL if it's an S3 URL
                    if notice.pdf_file_path.startswith('https://') and 's3' in notice.pdf_file_path:
                        # Parse S3 URL to get key
                        # Format: https://bucket.s3.region.amazonaws.com/key
                        url_parts = notice.pdf_file_path.split('/')
                        s3_key = '/'.join(url_parts[3:])  # Everything after bucket/s3/region/
                        delete_result = s3_storage.delete_object(s3_key)
                        if delete_result['success']:
                            deleted_files.append(s3_key)
                            logger.info(f"Deleted S3 file: {s3_key}")
                        else:
                            failed_deletions.append(s3_key)
                            logger.warning(f"Failed to delete S3 file: {s3_key}")
                    else:
                        logger.info(f"Skipping non-S3 file path: {notice.pdf_file_path}")
                        
                except Exception as s3_error:
                    logger.error(f"Error deleting S3 file for notice {notice.notice_id}: {str(s3_error)}")
                    failed_deletions.append(notice.pdf_file_path)
            
            # Delete the notice from database
            db.delete(notice)
        
        # Delete associated document records if any
        if notices:
            for notice in notices:
                if notice.document_id:
                    document = db.query(Document).filter(Document.document_id == notice.document_id).first()
                    if document:
                        db.delete(document)
        
        # Delete all LP payments associated with this drawdown
        lp_payments = db.query(LPPayment).filter(LPPayment.drawdown_id == drawdown_id).all()
        deleted_payments_count = len(lp_payments)
        
        for lp_payment in lp_payments:
            logger.info(f"Deleting LP payment {lp_payment.lp_payment_id} for drawdown {drawdown_id}")
            db.delete(lp_payment)
        
        # Delete the drawdown itself
        db.delete(drawdown)
        
        # Commit all deletions
        db.commit()
        
        logger.info(f"Successfully deleted drawdown {drawdown_id} with {len(notices)} notices and {deleted_payments_count} LP payments")
        
        return {
            "success": True,
            "message": f"Drawdown {drawdown_id} and associated records deleted successfully",
            "deleted_notices": len(notices),
            "deleted_lp_payments": deleted_payments_count,
            "deleted_s3_files": len(deleted_files),
            "failed_s3_deletions": len(failed_deletions),
            "s3_files_deleted": deleted_files,
            "s3_files_failed": failed_deletions
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting drawdown {drawdown_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting drawdown: {str(e)}")

@router.get("/{drawdown_id}/status")
def get_drawdown_status(
    drawdown_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get drawdown status
    """
    try:
        drawdown = db.query(LPDrawdown).filter(LPDrawdown.drawdown_id == drawdown_id).first()
        
        if not drawdown:
            raise HTTPException(status_code=404, detail=f"Drawdown {drawdown_id} not found")
        
        return {"status": drawdown.status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drawdown status {drawdown_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting drawdown status: {str(e)}")

@router.patch("/{drawdown_id}")
def update_drawdown(
    drawdown_id: str,
    request: DrawdownUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update any drawdown field
    """
    try:
        drawdown = db.query(LPDrawdown).filter(LPDrawdown.drawdown_id == drawdown_id).first()
        
        if not drawdown:
            raise HTTPException(status_code=404, detail=f"Drawdown {drawdown_id} not found")
        
        # Valid status values (only validate if status is being updated)
        valid_statuses = [status.value for status in DrawdownNoticeStatus]
        
        # Track changes for response
        changes = {}
        
        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(drawdown, field):
                # Special validation for status
                if field == "status" and value not in valid_statuses:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid status. Valid values are: {', '.join(valid_statuses)}"
                    )
                
                old_value = getattr(drawdown, field)
                if old_value != value:
                    setattr(drawdown, field, value)
                    changes[field] = {"old": old_value, "new": value}
        
        if not changes:
            return {
                "drawdown_id": str(drawdown_id),
                "message": "No changes made - all provided values were the same as current values",
                "changes": {}
            }
        
        db.commit()
        db.refresh(drawdown)
        
        logger.info(f"Updated drawdown {drawdown_id} - Changed fields: {list(changes.keys())}")
        
        return {
            "drawdown_id": str(drawdown_id),
            "message": f"Successfully updated {len(changes)} field(s)",
            "changes": changes,
            "updated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating drawdown {drawdown_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating drawdown: {str(e)}")

@router.patch("/{drawdown_id}/status")
def update_drawdown_status(
    drawdown_id: str,
    request: DrawdownStatusUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update drawdown status (legacy endpoint - use PATCH /{drawdown_id} instead)
    """
    try:
        # Convert to the new format and use the comprehensive update
        update_request = DrawdownUpdateRequest(
            status=request.new_status,
            notes=request.notes
        )
        
        return update_drawdown(drawdown_id, update_request, current_user, db)
        
    except Exception as e:
        logger.error(f"Error in legacy status update {drawdown_id}: {str(e)}")
        raise


@router.get("/due_date", response_model=List[str])
def get_drawdowns_by_due_date(
    start_date: date = Query(..., description="Start date for due date range"),
    end_date: date = Query(..., description="End date for due date range"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of LP IDs with drawdowns due in date range
    """
    try:
        drawdowns = db.query(LPDrawdown).filter(
            and_(
                LPDrawdown.drawdown_due_date >= start_date,
                LPDrawdown.drawdown_due_date <= end_date,
                LPDrawdown.status != "Cancelled"
            )
        ).all()
        
        lp_ids = [str(d.lp_id) for d in drawdowns]
        
        return lp_ids
        
    except Exception as e:
        logger.error(f"Error getting drawdowns by due date: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting drawdowns by due date: {str(e)}")