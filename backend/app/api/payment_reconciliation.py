"""
Payment Reconciliation API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, datetime
import logging

from ..database.base import get_db
from ..auth.security import get_current_user
from ..models import LPPayment, PaymentReconciliation, LPDetails, LPDrawdown, FundDetails
from ..schemas.payment_reconciliation import (
    PaymentReconciliationUploadRequest,
    PaymentReconciliationUploadResponse,
    ManualPaymentRecordRequest,
    ManualPaymentRecordResponse,
    PaymentReconciliationUpdateRequest,
    PaymentReconciliationUpdateResponse,
    PaymentReconciliationDeleteResponse,
    PaymentReconciliationListResponse,
    LPPaymentResponse,
    LPPaymentSummary
)
from ..services.payment_reconciliation_service import PaymentReconciliationService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload-statement", response_model=PaymentReconciliationUploadResponse)
async def upload_bank_statement(
    bank_statement: UploadFile = File(...),
    fund_id: int = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload bank statement PDF and process payments using LLM
    
    This endpoint:
    1. Validates the uploaded PDF file
    2. Extracts text from the bank statement
    3. Uses LLM to identify and match payments
    4. Creates LP_PAYMENTS records
    5. Updates drawdown notice statuses for paid LPs
    6. Returns reconciliation summary
    """
    try:
        # Validate file
        if bank_statement.content_type != "application/pdf":
            raise HTTPException(
                status_code=400, 
                detail="File must be a PDF"
            )
        
        # Read file content
        pdf_content = await bank_statement.read()
        if len(pdf_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )
        
        # Validate fund exists
        fund = db.query(FundDetails).filter(FundDetails.fund_id == fund_id).first()
        if not fund:
            raise HTTPException(
                status_code=404,
                detail=f"Fund with ID {fund_id} not found"
            )
        
        # Process with service
        service = PaymentReconciliationService(db)
        # Extract filename without extension for S3 upload
        filename = bank_statement.filename.rsplit('.', 1)[0] if bank_statement.filename else "bank_statement"
        reconciliation, payments, per_lp_results = service.process_bank_statement_with_llm(
            pdf_content, fund_id, filename
        )
        
        # Commit changes
        db.commit()
        
        # Refresh objects
        db.refresh(reconciliation)
        
        logger.info(f"Processed bank statement for fund {fund_id}. "
                   f"Created {len(payments)} payment records, matched {reconciliation.matched_payments}")
        
        return PaymentReconciliationUploadResponse(
            payment_id=reconciliation.payment_id,
            fund_id=fund_id,
            drawdown_quarter=reconciliation.drawdown_quarter,
            total_expected=reconciliation.total_expected,
            total_received=reconciliation.total_received,
            overall_status=reconciliation.overall_status,
            processed_payments=reconciliation.processed_payments,
            matched_payments=reconciliation.matched_payments,
            created_at=reconciliation.created_at,
            per_lp=[LPPaymentSummary(**lp_data) for lp_data in per_lp_results]
        )
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing bank statement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing bank statement: {str(e)}")

@router.post("/manual-record", response_model=ManualPaymentRecordResponse)
def manual_record_payment(
    request: ManualPaymentRecordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually record a payment without uploading statement
    
    This endpoint:
    1. Validates LP and fund relationship
    2. Gets expected amount from drawdown
    3. Calculates payment status
    4. Creates LP_PAYMENTS record
    5. Updates drawdown status if payment is complete
    """
    try:
        service = PaymentReconciliationService(db)
        payment, drawdown_status_updated = service.manual_record_payment(
            lp_id=request.lp_id,
            fund_id=request.fund_id,
            drawdown_quarter=request.drawdown_quarter,
            paid_amount=request.paid_amount,
            payment_date=request.payment_date,
            notes=request.notes
        )
        
        db.commit()
        db.refresh(payment)
        
        # Calculate amount_check
        amount_check = payment.status == "Paid"
        
        logger.info(f"Manually recorded payment {payment.lp_payment_id} for LP {request.lp_id}")
        
        return ManualPaymentRecordResponse(
            success=True,
            lp_payment_id=payment.lp_payment_id,
            message="Payment recorded successfully",
            status=payment.status,
            amount_check=amount_check,
            drawdown_status_updated=drawdown_status_updated,
            created_at=payment.created_at
        )
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error recording manual payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recording payment: {str(e)}")

@router.get("/", response_model=PaymentReconciliationListResponse)
def list_payment_reconciliations(
    fund_id: Optional[int] = Query(None, description="Filter by fund ID"),
    lp_id: Optional[str] = Query(None, description="Filter by LP ID"),
    drawdown_id: Optional[str] = Query(None, description="Filter by drawdown ID"),
    quarter: Optional[str] = Query(None, description="Filter by quarter"),
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_date_from: Optional[date] = Query(None, description="Filter payments from date"),
    payment_date_to: Optional[date] = Query(None, description="Filter payments to date"),
    amount_min: Optional[Decimal] = Query(None, ge=0, description="Minimum payment amount"),
    amount_max: Optional[Decimal] = Query(None, ge=0, description="Maximum payment amount"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List payment reconciliations with filtering and pagination
    """
    try:
        query = db.query(LPPayment).options(
            joinedload(LPPayment.lp),
            joinedload(LPPayment.drawdown),
            joinedload(LPPayment.fund),
            joinedload(LPPayment.payment_reconciliation)
        )
        
        # Apply filters
        if fund_id:
            query = query.filter(LPPayment.fund_id == fund_id)
        if lp_id:
            query = query.filter(LPPayment.lp_id == lp_id)
        if drawdown_id:
            query = query.filter(LPPayment.drawdown_id == drawdown_id)
        if quarter:
            query = query.filter(LPPayment.quarter == quarter)
        if status:
            query = query.filter(LPPayment.status == status)
        if payment_date_from:
            query = query.filter(LPPayment.payment_date >= payment_date_from)
        if payment_date_to:
            query = query.filter(LPPayment.payment_date <= payment_date_to)
        if amount_min is not None:
            query = query.filter(LPPayment.paid_amount >= amount_min)
        if amount_max is not None:
            query = query.filter(LPPayment.paid_amount <= amount_max)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        payments = query.order_by(desc(LPPayment.created_at)).offset(skip).limit(limit).all()
        
        # Convert to response format
        payment_responses = []
        for payment in payments:
            # Get S3 link from payment reconciliation if available
            payment_s3_link = None
            if payment.payment_reconciliation:
                payment_s3_link = payment.payment_reconciliation.payment_s3_link
            
            payment_responses.append(LPPaymentResponse(
                lp_payment_id=payment.lp_payment_id,
                lp_id=str(payment.lp_id),
                lp_name=payment.lp.lp_name,
                drawdown_id=str(payment.drawdown_id),
                payment_id=payment.payment_id,
                payment_s3_link=payment_s3_link,
                paid_amount=payment.paid_amount,
                payment_date=payment.payment_date,
                fund_id=payment.fund_id,
                quarter=payment.quarter,
                amount_due=payment.amount_due,
                status=payment.status,
                notes=payment.notes,
                created_at=payment.created_at
            ))
        
        logger.info(f"Listed {len(payment_responses)} payments out of {total_count} total")
        
        return PaymentReconciliationListResponse(
            payments=payment_responses,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing payments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing payments: {str(e)}")

@router.patch("/{lp_payment_id}", response_model=PaymentReconciliationUpdateResponse)
def update_payment_reconciliation(
    lp_payment_id: int,
    request: PaymentReconciliationUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update payment reconciliation record and handle status changes
    
    Automatically updates drawdown status when payment status changes to 'Paid'
    """
    try:
        service = PaymentReconciliationService(db)
        
        # Convert request to dict, excluding unset fields
        update_data = request.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )
        
        payment, drawdown_status_updated, updated_fields = service.update_payment_and_status(
            lp_payment_id, update_data
        )
        
        db.commit()
        db.refresh(payment)
        
        logger.info(f"Updated payment {lp_payment_id} - Fields: {updated_fields}")
        
        return PaymentReconciliationUpdateResponse(
            success=True,
            message=f"Successfully updated {len(updated_fields)} field(s)",
            lp_payment_id=lp_payment_id,
            updated_fields=updated_fields,
            drawdown_status_updated=drawdown_status_updated,
            updated_at=payment.updated_at
        )
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating payment {lp_payment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating payment: {str(e)}")

@router.delete("/{lp_payment_id}", response_model=PaymentReconciliationDeleteResponse)
def delete_payment_reconciliation(
    lp_payment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete payment reconciliation record
    """
    try:
        payment = db.query(LPPayment).filter(LPPayment.lp_payment_id == lp_payment_id).first()
        
        if not payment:
            raise HTTPException(
                status_code=404,
                detail=f"Payment {lp_payment_id} not found"
            )
        
        db.delete(payment)
        db.commit()
        
        logger.info(f"Deleted payment {lp_payment_id}")
        
        return PaymentReconciliationDeleteResponse(
            success=True,
            message="LP payment record deleted successfully",
            lp_payment_id=lp_payment_id
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting payment {lp_payment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting payment: {str(e)}")

@router.get("/{payment_id}")
def get_payment_reconciliation(
    payment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific payment reconciliation details
    """
    try:
        reconciliation = db.query(PaymentReconciliation).filter(
            PaymentReconciliation.payment_id == payment_id
        ).first()
        
        if not reconciliation:
            raise HTTPException(
                status_code=404,
                detail=f"Payment reconciliation {payment_id} not found"
            )
        
        return {
            "payment_id": reconciliation.payment_id,
            "fund_id": reconciliation.fund_id,
            "drawdown_quarter": reconciliation.drawdown_quarter,
            "total_expected": reconciliation.total_expected,
            "total_received": reconciliation.total_received,
            "overall_status": reconciliation.overall_status,
            "processed_payments": reconciliation.processed_payments,
            "matched_payments": reconciliation.matched_payments,
            "created_at": reconciliation.created_at,
            "updated_at": reconciliation.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reconciliation {payment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting reconciliation: {str(e)}")

@router.delete("/reconciliation/{payment_id}")
def delete_payment_reconciliation(
    payment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete payment reconciliation and all associated LP payments
    
    This endpoint:
    1. Deletes all LP payments associated with the reconciliation
    2. Deletes the bank statement PDF from S3 (if exists)
    3. Deletes the payment reconciliation record
    4. Returns summary of deleted records
    """
    try:
        service = PaymentReconciliationService(db)
        deletion_result = service.delete_payment_reconciliation(payment_id)
        
        # Commit the deletions
        db.commit()
        
        logger.info(f"Successfully deleted payment reconciliation {payment_id} and {deletion_result['lp_payments_count']} associated LP payments")
        
        return {
            "success": True,
            "message": f"Successfully deleted payment reconciliation {payment_id}",
            "deleted_reconciliation": deletion_result["reconciliation"],
            "deleted_lp_payments": deletion_result["deleted_lp_payments"],
            "lp_payments_count": deletion_result["lp_payments_count"],
            "s3_file_deleted": deletion_result["s3_file_deleted"]
        }
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting payment reconciliation {payment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting payment reconciliation: {str(e)}") 