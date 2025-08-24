from typing import List, Dict, Tuple, Optional, Any
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
import json
from io import BytesIO
import tempfile

from ..models import (
    LPPayment, LPPaymentStatus, PaymentReconciliation, PaymentReconciliationStatus,
    LPDetails, LPDrawdown, DrawdownNotice, DrawdownNoticeStatus, FundDetails
)
from ..api.drawdowns import calculate_quarter_string
from ..schemas.payment_reconciliation import LLMProcessingResult, LLMPaymentExtraction
from ..utils.llm import get_response_from_openai
from ..utils.pdf_extractor import extract_text_from_pdf
from ..utils.s3_storage import get_s3_storage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from prompts.payment_reconillation.payment_reconcillation import (
    payment_reconcillation_system_prompt,
    payment_reconcillation_user_prompt
)

logger = logging.getLogger(__name__)

class PaymentReconciliationService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def upload_bank_statement_to_s3(
        self, 
        pdf_content: bytes, 
        fund_name: str, 
        quarter: str,
        filename: str = "bank_statement"
    ) -> Optional[str]:
        """Upload bank statement PDF to S3 and return the S3 URL"""
        temp_pdf_path = None
        try:
            s3_storage = get_s3_storage()
            
            # Create timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Sanitize fund name for S3 key
            safe_fund_name = "".join(c for c in fund_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_fund_name = safe_fund_name.replace(' ', '_')
            
            # S3 key: FundScheme/Quarter/Bank Statements/bank_statement_timestamp.pdf
            s3_key = f"{safe_fund_name}/{quarter}/Bank Statements/{filename}_{timestamp}.pdf"
            
            # Create temporary file to store PDF content (following drawdowns pattern)
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_pdf_path = temp_file.name
            
            # Prepare metadata
            metadata = {
                'document_type': 'bank_statement',
                'quarter': quarter,
                'fund_name': fund_name,
                'upload_timestamp': timestamp
            }
            
            # Upload to S3 using local file path (following drawdowns pattern)
            upload_result = s3_storage.upload_file(
                local_file_path=temp_pdf_path,
                s3_key=s3_key,
                metadata=metadata,
                content_type='application/pdf'
            )
            
            if upload_result['success']:
                logger.info(f"Successfully uploaded bank statement to S3: {s3_key}")
                return upload_result['s3_url']
            else:
                logger.error(f"Failed to upload bank statement to S3: {upload_result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading bank statement to S3: {str(e)}")
            return None
        finally:
            # Clean up temporary file
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file {temp_pdf_path}: {cleanup_error}")
    
    def calculate_payment_status(self, paid_amount: Decimal, expected_amount: Decimal) -> str:
        """Calculate payment status based on amounts"""
        if paid_amount == expected_amount:
            return LPPaymentStatus.PAID.value
        elif paid_amount < expected_amount:
            return LPPaymentStatus.SHORTFALL.value
        else:
            return LPPaymentStatus.OVER_PAYMENT.value
    
    def update_drawdown_status_if_paid(self, lp_id: str, fund_id: int, quarter: str) -> bool:
        """Update drawdown notice and LP drawdown status to ALLOTMENT_SHEET_GENERATION_PENDING if payment is complete"""
        updated = False
        
        try:
            # Update DrawdownNotice status
            drawdown_notice = self.db.query(DrawdownNotice).join(LPDrawdown).filter(
                and_(
                    LPDrawdown.lp_id == lp_id,
                    LPDrawdown.fund_id == fund_id,
                    LPDrawdown.drawdown_quarter == quarter,
                    DrawdownNotice.status == DrawdownNoticeStatus.DRAWDOWN_PAYMENT_PENDING.value
                )
            ).first()
            
            if drawdown_notice:
                drawdown_notice.status = DrawdownNoticeStatus.ALLOTMENT_SHEET_GENERATION_PENDING.value
                updated = True
                logger.info(f"Updated DrawdownNotice {drawdown_notice.notice_id} status to ALLOTMENT_SHEET_GENERATION_PENDING")
            
            # Update LPDrawdown status
            lp_drawdown = self.db.query(LPDrawdown).filter(
                and_(
                    LPDrawdown.lp_id == lp_id,
                    LPDrawdown.fund_id == fund_id,
                    LPDrawdown.drawdown_quarter == quarter,
                    LPDrawdown.status == DrawdownNoticeStatus.DRAWDOWN_PAYMENT_PENDING.value
                )
            ).first()
            
            if lp_drawdown:
                lp_drawdown.status = DrawdownNoticeStatus.ALLOTMENT_SHEET_GENERATION_PENDING.value
                updated = True
                logger.info(f"Updated LPDrawdown {lp_drawdown.drawdown_id} status to ALLOTMENT_SHEET_GENERATION_PENDING")
                
        except Exception as e:
            logger.error(f"Error updating drawdown status: {str(e)}")
            
        return updated
    
    def manual_record_payment(
        self, 
        lp_id: str, 
        fund_id: int, 
        drawdown_quarter: str,
        paid_amount: Decimal,
        payment_date: date,
        notes: Optional[str] = None
    ) -> Tuple[LPPayment, bool]:
        """Manually record a payment and update statuses"""
        
        # Validate LP exists and belongs to fund
        lp = self.db.query(LPDetails).filter(
            and_(LPDetails.lp_id == lp_id, LPDetails.fund_id == fund_id)
        ).first()
        
        if not lp:
            raise ValueError(f"LP {lp_id} not found for fund {fund_id}")
        
        # Get expected amount from drawdown
        drawdown = self.db.query(LPDrawdown).filter(
            and_(
                LPDrawdown.lp_id == lp_id,
                LPDrawdown.fund_id == fund_id,
                LPDrawdown.drawdown_quarter == drawdown_quarter
            )
        ).first()
        
        if not drawdown:
            raise ValueError(f"No drawdown found for LP {lp_id}, fund {fund_id}, quarter {drawdown_quarter}")
        
        # Check for duplicate payment (same LP, quarter, date, and amount)
        existing_payment = self.db.query(LPPayment).filter(
            and_(
                LPPayment.lp_id == lp_id,
                LPPayment.quarter == drawdown_quarter,
                LPPayment.payment_date == payment_date,
                LPPayment.paid_amount == paid_amount
            )
        ).first()
        
        if existing_payment:
            raise ValueError(f"Duplicate payment already exists for LP {lp_id}, quarter {drawdown_quarter}, "
                           f"date {payment_date}, amount {paid_amount}")
        
        expected_amount = drawdown.drawdown_amount
        status = self.calculate_payment_status(paid_amount, expected_amount)
        
        # Create payment record
        payment = LPPayment(
            lp_id=lp_id,
            drawdown_id=drawdown.drawdown_id,
            fund_id=fund_id,
            quarter=drawdown_quarter,
            paid_amount=paid_amount,
            payment_date=payment_date,
            amount_due=expected_amount,
            status=status,
            notes=notes or "Manual entry"
        )
        
        self.db.add(payment)
        self.db.flush()  # Get the payment ID
        
        # Update drawdown status if payment is complete
        drawdown_status_updated = False
        if status == LPPaymentStatus.PAID.value:
            drawdown_status_updated = self.update_drawdown_status_if_paid(lp_id, fund_id, drawdown_quarter)
        
        return payment, drawdown_status_updated
    
    def process_bank_statement_with_llm(
        self, 
        pdf_content: bytes, 
        fund_id: int,
        filename: str = "bank_statement"
    ) -> Tuple[PaymentReconciliation, List[LPPayment], List[Dict]]:
        """Process bank statement PDF using LLM and create payment records"""
        
        # Create temporary file to store PDF content
        temp_pdf_path = None
        try:
            # Create temporary file with .pdf extension
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_pdf_path = temp_file.name
            
            # Extract text from PDF using file path
            account_statement, _, _ = extract_text_from_pdf(temp_pdf_path)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            # Clean up temporary file if it was created
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                except:
                    pass
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
        
        finally:
            # Clean up temporary file
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file {temp_pdf_path}: {cleanup_error}")
        
        # Get LP list for the fund
        lps = self.db.query(LPDetails).filter(LPDetails.fund_id == fund_id).all()
        if not lps:
            raise ValueError(f"No LPs found for fund {fund_id}")
        
        db_lp_list = [lp.lp_name for lp in lps]
        
        # Create LLM prompt
        user_prompt = payment_reconcillation_user_prompt.format(
            account_statement=account_statement,
            db_lp_list=json.dumps({"db_lp_list": db_lp_list})
        )
        
        # Call LLM
        try:
            llm_response = get_response_from_openai(
                system_prompt=payment_reconcillation_system_prompt,
                user_prompt=user_prompt
            )
            
            # Parse LLM response
            llm_result = json.loads(llm_response)
            extracted_payments = LLMProcessingResult(**llm_result)
            
        except Exception as e:
            logger.error(f"LLM processing failed: {str(e)}")
            raise ValueError(f"Failed to process bank statement with LLM: {str(e)}")
        
        # Get all drawdowns for this fund (we'll match by quarter per payment)
        all_drawdowns = self.db.query(LPDrawdown).filter(LPDrawdown.fund_id == fund_id).all()
        
        if not all_drawdowns:
            raise ValueError(f"No drawdowns found for fund {fund_id}")
        
        # Create a mapping of (LP name, quarter) to drawdowns
        lp_quarter_to_drawdown = {}
        for drawdown in all_drawdowns:
            lp = self.db.query(LPDetails).filter(LPDetails.lp_id == drawdown.lp_id).first()
            if lp:
                key = (lp.lp_name, drawdown.drawdown_quarter)
                lp_quarter_to_drawdown[key] = drawdown
        
        # Process extracted payments
        created_payments = []
        per_lp_results = []
        total_received = Decimal('0')
        matched_payments = 0
        quarters_processed = set()
        
        for extraction in extracted_payments.results:
            try:
                # Parse payment date and determine quarter
                try:
                    payment_date = datetime.strptime(extraction.payment_date, "%Y-%m-%d").date()
                    payment_quarter = calculate_quarter_string(payment_date)
                except ValueError:
                    logger.warning(f"Invalid payment date format: {extraction.payment_date}")
                    continue
                
                quarters_processed.add(payment_quarter)
                
                # Find matching drawdown using LP name and calculated quarter
                drawdown_key = (extraction.db_lp_name, payment_quarter)
                drawdown = lp_quarter_to_drawdown.get(drawdown_key)
                if not drawdown:
                    logger.warning(f"No drawdown found for LP: {extraction.db_lp_name}, quarter: {payment_quarter}")
                    continue
                
                # Check for duplicate payment (same LP, quarter, date, and amount)
                existing_payment = self.db.query(LPPayment).filter(
                    and_(
                        LPPayment.lp_id == drawdown.lp_id,
                        LPPayment.quarter == payment_quarter,
                        LPPayment.payment_date == payment_date,
                        LPPayment.paid_amount == extraction.credit_amount
                    )
                ).first()
                
                if existing_payment:
                    logger.info(f"Skipping duplicate payment for LP {extraction.db_lp_name}, quarter {payment_quarter}, "
                               f"date {payment_date}, amount {extraction.credit_amount}")
                    continue
                
                # Calculate status
                status = self.calculate_payment_status(extraction.credit_amount, drawdown.drawdown_amount)
                
                # Create payment record
                payment = LPPayment(
                    lp_id=drawdown.lp_id,
                    drawdown_id=drawdown.drawdown_id,
                    fund_id=fund_id,
                    quarter=payment_quarter,
                    paid_amount=extraction.credit_amount,
                    payment_date=payment_date,
                    amount_due=drawdown.drawdown_amount,
                    status=status,
                    notes=f"Automatic extraction: {extraction.reasoning}"
                )
                
                self.db.add(payment)
                self.db.flush()
                created_payments.append(payment)
                
                # Update drawdown status if paid
                drawdown_status_updated = False
                if status == LPPaymentStatus.PAID.value:
                    drawdown_status_updated = self.update_drawdown_status_if_paid(
                        str(drawdown.lp_id), fund_id, payment_quarter
                    )
                    matched_payments += 1
                
                # Add to per_lp results
                lp = self.db.query(LPDetails).filter(LPDetails.lp_id == drawdown.lp_id).first()
                per_lp_results.append({
                    "lp_id": str(drawdown.lp_id),  # Return actual UUID
                    "lp_name": lp.lp_name,
                    "expected": drawdown.drawdown_amount,
                    "received": extraction.credit_amount,
                    "status": status,
                    "drawdown_status_updated": drawdown_status_updated
                })
                
                total_received += extraction.credit_amount
                
            except Exception as e:
                logger.error(f"Error processing payment for {extraction.db_lp_name}: {str(e)}")
                continue
        
        # Check if any new payments were actually created
        if not created_payments:
            logger.warning(f"No new payments created for fund {fund_id} - all payments were duplicates or no matches found")
            raise ValueError("No new payments were created. All payments in the bank statement already exist or no matching LPs were found.")
        
        # Calculate total expected for all quarters processed
        total_expected = Decimal('0')
        for quarter in quarters_processed:
            quarter_drawdowns = [d for d in all_drawdowns if d.drawdown_quarter == quarter]
            total_expected += sum(d.drawdown_amount for d in quarter_drawdowns)
        
        # Use sorted list of quarters processed
        quarters_list = sorted(list(quarters_processed)) if quarters_processed else ["N/A"]
        drawdown_quarters_string = ", ".join(quarters_list)
        
        # Get fund details for S3 upload
        fund = self.db.query(FundDetails).filter(FundDetails.fund_id == fund_id).first()
        fund_name = fund.scheme_name if fund else f"Fund_{fund_id}"
        
        # Upload bank statement to S3 (only if we have new payments)
        s3_url = self.upload_bank_statement_to_s3(
            pdf_content=pdf_content,
            fund_name=fund_name,
            quarter=drawdown_quarters_string,
            filename=filename
        )
        
        # Create reconciliation record
        overall_status = PaymentReconciliationStatus.COMPLETED.value if matched_payments > 0 else PaymentReconciliationStatus.IN_PROGRESS.value
        
        reconciliation = PaymentReconciliation(
            fund_id=fund_id,
            drawdown_quarter=drawdown_quarters_string,
            total_expected=total_expected,
            total_received=total_received,
            overall_status=overall_status,
            processed_payments=len(extracted_payments.results),
            matched_payments=matched_payments,
            payment_s3_link=s3_url
        )
        
        self.db.add(reconciliation)
        self.db.flush()  # Get the reconciliation payment_id
        
        # Update all created payments to reference this reconciliation
        for payment in created_payments:
            payment.payment_id = reconciliation.payment_id
        
        return reconciliation, created_payments, per_lp_results
    
    def update_payment_and_status(
        self,
        lp_payment_id: int,
        update_data: Dict
    ) -> Tuple[LPPayment, bool, List[str]]:
        """Update payment record and handle status changes"""
        
        payment = self.db.query(LPPayment).filter(LPPayment.lp_payment_id == lp_payment_id).first()
        if not payment:
            raise ValueError(f"Payment {lp_payment_id} not found")
        
        updated_fields = []
        original_status = payment.status
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(payment, field) and value is not None:
                old_value = getattr(payment, field)
                if old_value != value:
                    setattr(payment, field, value)
                    updated_fields.append(field)
        
        # Update timestamp
        payment.updated_at = datetime.utcnow()
        
        # Check if status changed to Paid
        drawdown_status_updated = False
        if ('status' in updated_fields and 
            payment.status == LPPaymentStatus.PAID.value and 
            original_status != LPPaymentStatus.PAID.value):
            
            drawdown_status_updated = self.update_drawdown_status_if_paid(
                str(payment.lp_id), payment.fund_id, payment.quarter
            )
        
        return payment, drawdown_status_updated, updated_fields
    
    def delete_payment_reconciliation(self, payment_id: int) -> Dict[str, Any]:
        """Delete payment reconciliation and all associated LP payments"""
        
        # Get the reconciliation record
        reconciliation = self.db.query(PaymentReconciliation).filter(
            PaymentReconciliation.payment_id == payment_id
        ).first()
        
        if not reconciliation:
            raise ValueError(f"Payment reconciliation {payment_id} not found")
        
        # Get all associated LP payments
        lp_payments = self.db.query(LPPayment).filter(
            LPPayment.payment_id == payment_id
        ).all()
        
        deleted_lp_payments = []
        
        # Delete all LP payments first (cascade delete)
        for lp_payment in lp_payments:
            deleted_lp_payments.append({
                "lp_payment_id": lp_payment.lp_payment_id,
                "lp_name": lp_payment.lp.lp_name if lp_payment.lp else "Unknown",
                "paid_amount": lp_payment.paid_amount,
                "quarter": lp_payment.quarter
            })
            self.db.delete(lp_payment)
        
        # Store reconciliation info before deletion
        reconciliation_info = {
            "payment_id": reconciliation.payment_id,
            "fund_id": reconciliation.fund_id,
            "drawdown_quarter": reconciliation.drawdown_quarter,
            "total_expected": reconciliation.total_expected,
            "total_received": reconciliation.total_received,
            "payment_s3_link": reconciliation.payment_s3_link,
            "processed_payments": reconciliation.processed_payments,
            "matched_payments": reconciliation.matched_payments
        }
        
        # Delete S3 file if it exists
        s3_deletion_success = False
        if reconciliation.payment_s3_link:
            try:
                s3_storage = get_s3_storage()
                # Extract S3 key from URL
                if reconciliation.payment_s3_link.startswith('https://') and 's3' in reconciliation.payment_s3_link:
                    # Parse S3 URL to get key
                    url_parts = reconciliation.payment_s3_link.split('/')
                    s3_key = '/'.join(url_parts[3:])  # Everything after bucket/s3/region/
                    delete_result = s3_storage.delete_object(s3_key)
                    s3_deletion_success = delete_result.get('success', False)
                    if s3_deletion_success:
                        logger.info(f"Deleted S3 file: {s3_key}")
                    else:
                        logger.warning(f"Failed to delete S3 file: {s3_key}")
            except Exception as e:
                logger.error(f"Error deleting S3 file: {str(e)}")
        
        # Delete the reconciliation record
        self.db.delete(reconciliation)
        
        return {
            "reconciliation": reconciliation_info,
            "deleted_lp_payments": deleted_lp_payments,
            "lp_payments_count": len(deleted_lp_payments),
            "s3_file_deleted": s3_deletion_success
        } 