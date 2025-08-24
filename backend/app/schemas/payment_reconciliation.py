from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

# Request schemas
class PaymentReconciliationUploadRequest(BaseModel):
    fund_id: int

class ManualPaymentRecordRequest(BaseModel):
    lp_id: str
    fund_id: int
    drawdown_quarter: str
    paid_amount: Decimal = Field(..., decimal_places=2)
    payment_date: date
    notes: Optional[str] = None

class PaymentReconciliationUpdateRequest(BaseModel):
    paid_amount: Optional[Decimal] = Field(None, decimal_places=2)
    payment_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ['Pending', 'Paid', 'Shortfall', 'Over-payment']
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

# Response schemas
class LPPaymentResponse(BaseModel):
    lp_payment_id: int
    lp_id: str
    lp_name: str
    drawdown_id: str
    payment_id: Optional[int] = None
    payment_s3_link: Optional[str] = None
    paid_amount: Decimal
    payment_date: date
    fund_id: int
    quarter: str
    amount_due: Decimal
    status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LPPaymentSummary(BaseModel):
    lp_id: str
    lp_name: str
    expected: Decimal
    received: Decimal
    status: str
    drawdown_status_updated: bool

class ManualPaymentRecordResponse(BaseModel):
    success: bool
    lp_payment_id: int
    message: str
    status: str
    amount_check: bool
    drawdown_status_updated: bool
    created_at: datetime

class PaymentReconciliationUploadResponse(BaseModel):
    payment_id: int
    fund_id: int
    drawdown_quarter: str
    total_expected: Decimal
    total_received: Decimal
    overall_status: str
    processed_payments: int
    matched_payments: int
    created_at: datetime
    per_lp: List[LPPaymentSummary]

class PaymentReconciliationListResponse(BaseModel):
    payments: List[LPPaymentResponse]
    total_count: int
    skip: int
    limit: int

class PaymentReconciliationUpdateResponse(BaseModel):
    success: bool
    message: str
    lp_payment_id: int
    updated_fields: List[str]
    drawdown_status_updated: bool
    updated_at: datetime

class PaymentReconciliationDeleteResponse(BaseModel):
    success: bool
    message: str
    lp_payment_id: int

# LLM Processing schemas
class LLMPaymentExtraction(BaseModel):
    reasoning: str
    db_lp_name: str
    payment_date: str
    credit_amount: Decimal
    quarter: str

class LLMProcessingResult(BaseModel):
    results: List[LLMPaymentExtraction] 