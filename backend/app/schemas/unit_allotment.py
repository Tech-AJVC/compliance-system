from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import date, datetime
import uuid

class UnitAllotmentBase(BaseModel):
    """Base schema for unit allotment with common fields"""
    clid: Optional[str] = None
    depository: Optional[str] = None
    dpid: Optional[str] = None
    first_holder_name: str
    first_holder_pan: Optional[str] = None
    second_holder_name: Optional[str] = None
    second_holder_pan: Optional[str] = None
    third_holder_name: Optional[str] = None
    third_holder_pan: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    micr_code: Optional[str] = None
    date_of_allotment: Optional[date] = None

class UnitAllotmentCreate(UnitAllotmentBase):
    """Schema for creating unit allotment - only requires fund_id, rest calculated"""
    fund_id: int

class UnitAllotmentCalculated(UnitAllotmentBase):
    """Schema for calculated unit allotment data"""
    drawdown_id: uuid.UUID
    lp_id: uuid.UUID
    fund_id: int
    mgmt_fees: Decimal
    committed_amt: Decimal
    amt_accepted: Decimal
    drawdown_amount: Decimal
    drawdown_date: date
    drawdown_quarter: str
    nav_value: int  # NAV as integer
    allotted_units: int
    stamp_duty: Decimal
    status: str = "Generated"

class UnitAllotmentResponse(UnitAllotmentCalculated):
    """Schema for unit allotment API responses"""
    allotment_id: int
    excel_file_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UnitAllotmentGenerateRequest(BaseModel):
    """Schema for generating unit allotments"""
    fund_id: int
    force_recalculation: bool = False

class UnitAllotmentGenerateResponse(BaseModel):
    """Schema for unit allotment generation response"""
    success: bool
    message: str
    allotments: list[UnitAllotmentResponse]
    excel_file_url: Optional[str] = None
    total_lps: int
    total_units_allocated: int
    total_amount_allocated: Decimal

class UnitAllotmentListResponse(BaseModel):
    """Schema for paginated unit allotment list"""
    allotments: list[UnitAllotmentResponse]
    total_count: int
    skip: int
    limit: int

class UnitAllotmentFilter(BaseModel):
    """Schema for filtering unit allotments"""
    fund_id: Optional[int] = None
    status: Optional[str] = None
    drawdown_quarter: Optional[str] = None
    lp_id: Optional[uuid.UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None