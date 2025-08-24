"""
Pydantic schemas for Drawdown operations
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

# Input schemas for API requests
class DrawdownGenerateRequest(BaseModel):
    """Request schema for generating drawdowns"""
    fund_id: int = Field(..., description="Fund ID to generate drawdowns for")
    percentage_drawdown: Decimal = Field(..., ge=0, le=100, description="Percentage drawdown (0-100)")
    notice_date: date = Field(..., description="Notice date for the capital call")
    due_date: date = Field(..., description="Due date for payment")
    forecast_next_quarter: Decimal = Field(..., ge=0, le=100, description="Forecast percentage for next quarter")

class DrawdownPreviewRequest(BaseModel):
    """Request schema for drawdown preview"""
    fund_id: int = Field(..., description="Fund ID to preview drawdowns for")
    percentage_drawdown: Decimal = Field(..., ge=0, le=100, description="Percentage drawdown (0-100)")
    notice_date: date = Field(..., description="Notice date for the capital call")
    due_date: date = Field(..., description="Due date for payment")
    forecast_next_quarter: Decimal = Field(..., ge=0, le=100, description="Forecast percentage for next quarter")

class DrawdownStatusUpdateRequest(BaseModel):
    """Request schema for updating drawdown status"""
    new_status: str = Field(..., description="New status for the drawdown")
    notes: Optional[str] = Field(None, description="Optional notes for the status change")

class DrawdownUpdateRequest(BaseModel):
    """Request schema for updating any drawdown field"""
    # Date fields
    notice_date: Optional[date] = Field(None, description="Notice date for the capital call")
    drawdown_due_date: Optional[date] = Field(None, description="Due date for payment")
    payment_received_date: Optional[date] = Field(None, description="Date payment was received")
    date_of_allotment: Optional[date] = Field(None, description="Date of unit allotment")
    
    # Percentage and amount fields
    drawdown_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentage drawdown (0-100)")
    committed_amt: Optional[Decimal] = Field(None, ge=0, description="Committed amount")
    drawdown_amount: Optional[Decimal] = Field(None, ge=0, description="Drawdown amount")
    amount_called_up: Optional[Decimal] = Field(None, ge=0, description="Amount called up")
    remaining_commitment: Optional[Decimal] = Field(None, ge=0, description="Remaining commitment")
    amt_accepted: Optional[Decimal] = Field(None, ge=0, description="Amount accepted")
    nav_value: Optional[Decimal] = Field(None, ge=0, description="NAV value")
    mgmt_fees: Optional[Decimal] = Field(None, ge=0, description="Management fees")
    stamp_duty: Optional[Decimal] = Field(None, ge=0, description="Stamp duty")
    
    # Forecast fields
    forecast_next_quarter: Optional[Decimal] = Field(None, ge=0, le=100, description="Forecast percentage for next quarter")
    forecast_next_quarter_period: Optional[str] = Field(None, description="Forecast quarter period")
    
    # Status and other fields
    status: Optional[str] = Field(None, description="Drawdown status")
    drawdown_quarter: Optional[str] = Field(None, description="Drawdown quarter")
    allotted_units: Optional[int] = Field(None, ge=0, description="Units allotted")
    reference_number: Optional[str] = Field(None, description="Reference number")
    notes: Optional[str] = Field(None, description="Notes")

# Response schemas
class LPDrawdownResponse(BaseModel):
    """Response schema for individual LP drawdown"""
    model_config = ConfigDict(from_attributes=True)
    
    drawdown_id: UUID
    fund_id: int
    lp_id: UUID
    notice_date: date
    drawdown_due_date: date
    drawdown_percentage: Decimal
    drawdown_quarter: str
    
    # Calculated amounts
    committed_amt: Decimal
    drawdown_amount: Decimal
    amount_called_up: Decimal
    remaining_commitment: Decimal
    
    # Forecast information
    forecast_next_quarter: Decimal
    forecast_next_quarter_period: str
    
    # Status
    status: str
    
    # Optional fields
    payment_received_date: Optional[date] = None
    amt_accepted: Optional[Decimal] = None
    allotted_units: Optional[int] = None
    nav_value: Optional[Decimal] = None
    date_of_allotment: Optional[date] = None
    mgmt_fees: Optional[Decimal] = None
    stamp_duty: Optional[Decimal] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

class DrawdownNoticeResponse(BaseModel):
    """Response schema for drawdown notice"""
    model_config = ConfigDict(from_attributes=True)
    
    notice_id: UUID
    drawdown_id: UUID
    lp_id: UUID
    notice_date: date
    amount_due: Decimal
    due_date: date
    pdf_file_path: Optional[str] = None
    document_id: Optional[UUID] = None
    status: str
    sent_at: Optional[datetime] = None
    delivery_channel: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class LPDrawdownPreview(BaseModel):
    """Preview schema for individual LP drawdown"""
    lp_id: UUID
    lp_name: str
    commitment_amount: Decimal
    drawdown_amount: Decimal
    amount_called_up: Decimal
    remaining_commitment: Decimal

class DrawdownPreviewResponse(BaseModel):
    """Response schema for drawdown preview"""
    preview_id: str
    total_drawdown_amount: Decimal
    lp_previews: List[LPDrawdownPreview]
    summary: dict
    sample_html_preview: Optional[str] = Field(None, description="HTML preview of capital call notice for first LP")

class DrawdownGenerateResponse(BaseModel):
    """Response schema for drawdown generation"""
    success: bool
    message: str
    drawdown_count: int
    fund_id: int
    drawdown_quarter: str
    total_amount: Decimal
    generated_pdfs: List[str] = Field(description="List of paths to generated PDF files")
    drawdowns: List[LPDrawdownResponse]

class DrawdownWithBankDetails(BaseModel):
    """Extended drawdown response with fund bank details for PDF generation"""
    model_config = ConfigDict(from_attributes=True)
    
    # Core drawdown fields
    drawdown_id: UUID
    lp_id: UUID
    notice_date: date
    drawdown_due_date: date
    drawdown_amount: Decimal
    committed_amt: Decimal
    amount_called_up: Decimal
    remaining_commitment: Decimal
    forecast_next_quarter: Decimal
    forecast_next_quarter_period: str
    status: str
    
    # LP details
    investor: str = Field(alias="lp_name")
    
    # Fund bank details
    bank_name: str
    ifsc: str = Field(alias="bank_ifsc")
    acct_name: str = Field(alias="bank_account_name")
    acct_number: str = Field(alias="bank_account_no")
    bank_contact: str = Field(alias="bank_contact_person")
    phone: str = Field(alias="bank_contact_phone")

class DrawdownListResponse(BaseModel):
    """Response schema for listing drawdowns"""
    drawdowns: List[LPDrawdownResponse]
    total_count: int
    skip: int
    limit: int

class DrawdownStatusHistoryResponse(BaseModel):
    """Response schema for drawdown status history"""
    drawdown_id: UUID
    status_history: List[dict]

class DrawdownSummaryResponse(BaseModel):
    """Response schema for drawdown summary statistics"""
    fund_id: int
    quarter: str
    total_lps: int
    total_amount: Decimal
    total_sent: int
    total_received: int
    total_pending: int
    avg_drawdown_amount: Decimal