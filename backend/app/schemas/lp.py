from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from pydantic import ConfigDict

# LP Details Schemas

# Define LP status options
class LPStatus(str, Enum):
    WAITING_FOR_KYC = "Waiting for KYC"
    CA_CML_PENDING = "Contribution Agreement/CML Pending"
    ACTIVE = "Active"
    
class LPDetailsBase(BaseModel):
    fund_id: Optional[int] = None  # Added fund reference
    lp_name: str
    mobile_no: Optional[str] = None
    email: EmailStr
    email_for_drawdowns: Optional[str] = None  # New field from UC-LP-4
    address: Optional[str] = None
    nominee: Optional[str] = None
    pan: Optional[str] = None
    dob: Optional[date] = None
    doi: Optional[date] = None
    gender: Optional[str] = None
    date_of_agreement: Optional[date] = None
    commitment_amount: Optional[float] = None
    acknowledgement_of_ppm: Optional[bool] = None
    dpid: Optional[str] = None
    client_id: Optional[str] = None
    cml: Optional[str] = None
    isin: Optional[str] = None
    class_of_shares: Optional[str] = None
    citizenship: Optional[str] = None
    type: Optional[str] = None
    geography: Optional[str] = None
    kyc_status: Optional[str] = None  # New field from UC-LP-4
    status: Optional[str] = "Waiting for KYC"  # Default status

class LPDetailsCreate(LPDetailsBase):
    pass

class LPDetailsUpdate(LPDetailsBase):
    fund_id: Optional[int] = None  # Explicitly added for updates
    lp_name: Optional[str] = None
    email: Optional[EmailStr] = None
    email_for_drawdowns: Optional[str] = None
    kyc_status: Optional[str] = None
    status: Optional[str] = None

class LPDetailsResponse(LPDetailsBase):
    lp_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# LP Document Schemas
class LPDocumentBase(BaseModel):
    lp_id: UUID
    document_id: UUID
    document_type: str  # KYC, CA, CML, etc.

class LPDocumentCreate(LPDocumentBase):
    pass

class LPDocumentResponse(LPDocumentBase):
    lp_document_id: UUID
    created_at: datetime
    document_details: Optional[dict] = None  # Will include document metadata

    model_config = ConfigDict(from_attributes=True)

# LP Status Schema
class LPStatusUpdate(BaseModel):
    status: LPStatus
    kyc_status: Optional[str] = None

class LPStatusResponse(BaseModel):
    lp_id: UUID
    status: str
    kyc_status: Optional[str] = None
    status_updated: bool
    updated_at: datetime

# LP Drawdown Schemas
class LPDrawdownBase(BaseModel):
    lp_id: UUID
    drawdown_date: date
    amount: float = Field(..., gt=0, description="Drawdown amount must be positive")
    drawdown_percentage: Optional[float] = Field(None, ge=0, le=100, description="Percentage between 0-100")
    payment_due_date: date
    payment_received_date: Optional[date] = None
    payment_status: str = "Pending"
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    fund_id: Optional[int] = None

class LPDrawdownCreate(LPDrawdownBase):
    pass

class LPDrawdownUpdate(BaseModel):
    drawdown_date: Optional[date] = None
    amount: Optional[float] = Field(None, gt=0, description="Drawdown amount must be positive")
    drawdown_percentage: Optional[float] = Field(None, ge=0, le=100, description="Percentage between 0-100")
    payment_due_date: Optional[date] = None
    payment_received_date: Optional[date] = None
    payment_status: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    fund_id: Optional[int] = None

class LPDrawdownResponse(LPDrawdownBase):
    drawdown_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Combined schemas
class LPWithDrawdowns(LPDetailsResponse):
    drawdowns: List[LPDrawdownResponse] = []

    model_config = ConfigDict(from_attributes=True)

# Document upload schema for API
class DocumentUploadRequest(BaseModel):
    document_type: str  # KYC, CA, CML
    file_name: str
    share_with_emails: Optional[List[str]] = None

# Paginated response schema for GET all LPs
class LPListResponse(BaseModel):
    data: List[LPDetailsResponse]
    total: int
    
    model_config = ConfigDict(from_attributes=True)
