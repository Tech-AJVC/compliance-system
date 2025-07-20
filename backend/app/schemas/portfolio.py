from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from pydantic import ConfigDict

# Portfolio Company Schemas

class PortfolioCompanyBase(BaseModel):
    startup_brand: str
    company_name: Optional[str] = None  # Will be extracted from SHA
    sector: Optional[str] = None
    product_description: Optional[str] = None
    registered_address: Optional[str] = None  # Will be extracted from SHA
    pan: Optional[str] = None
    isin: Optional[str] = None

class PortfolioCompanyCreate(PortfolioCompanyBase):
    pass

class PortfolioCompanyUpdate(BaseModel):
    startup_brand: Optional[str] = None
    company_name: Optional[str] = None
    sector: Optional[str] = None
    product_description: Optional[str] = None
    registered_address: Optional[str] = None
    pan: Optional[str] = None
    isin: Optional[str] = None

class PortfolioCompanyResponse(PortfolioCompanyBase):
    company_id: int
    company_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Portfolio Founder Schemas

class PortfolioFounderBase(BaseModel):
    founder_name: Optional[str] = None  # Will be extracted from SHA
    founder_email: str
    founder_role: str

class PortfolioFounderCreate(PortfolioFounderBase):
    company_id: int

class PortfolioFounderUpdate(BaseModel):
    founder_name: Optional[str] = None
    founder_email: Optional[str] = None
    founder_role: Optional[str] = None

class PortfolioFounderResponse(PortfolioFounderBase):
    founder_id: int
    company_id: int
    founder_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Portfolio Investment Schemas

class PortfolioInvestmentBase(BaseModel):
    fund_id: int
    amount_invested: Decimal
    termsheet_sign_date: Optional[date] = None
    sha_sign_date: Optional[date] = None  # Will be extracted from SHA
    funding_date: date
    funding_tat_days: Optional[int] = None  # Calculated field
    latest_valuation: Optional[Decimal] = None
    valuation_date: Optional[date] = None
    ec_sign_date: Optional[date] = None

class PortfolioInvestmentCreate(PortfolioInvestmentBase):
    company_id: int

class PortfolioInvestmentUpdate(BaseModel):
    fund_id: Optional[int] = None
    amount_invested: Optional[Decimal] = None
    termsheet_sign_date: Optional[date] = None
    sha_sign_date: Optional[date] = None
    funding_date: Optional[date] = None
    funding_tat_days: Optional[int] = None
    latest_valuation: Optional[Decimal] = None
    valuation_date: Optional[date] = None
    ec_sign_date: Optional[date] = None

class PortfolioInvestmentResponse(PortfolioInvestmentBase):
    investment_id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Portfolio Document Schemas

class PortfolioDocumentBase(BaseModel):
    document_type: str
    doc_link: Optional[str] = None

class PortfolioDocumentCreate(PortfolioDocumentBase):
    company_id: int
    document_id: UUID

class PortfolioDocumentUpdate(BaseModel):
    document_type: Optional[str] = None
    doc_link: Optional[str] = None

class PortfolioDocumentResponse(PortfolioDocumentBase):
    portfolio_document_id: int
    company_id: int
    document_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Portfolio Onboarding Input Schema (UI Fields Only)

class FounderInfo(BaseModel):
    """Founder information from UI"""
    email: str = Field(..., description="Founder's email address")
    role: str = Field(..., description="Founder's role in the company")

class PortfolioOnboardingInput(BaseModel):
    """
    Portfolio onboarding input schema containing only UI-provided fields.
    SHA-derived fields (company_name, registered_address, sha_sign_date) are handled separately.
    """
    
    # Company Information (from UI)
    startup_brand: str = Field(..., description="Brand/startup name of the company")
    sector: Optional[str] = Field(None, description="Business sector (e.g., Consumer, Technology)")
    pan: Optional[str] = Field(None, description="PAN number of the company")
    isin: Optional[str] = Field(None, description="ISIN number of the company")
    product_description: Optional[str] = Field(None, description="Description of the company's product/service")
    
    # Founders Information (from UI)
    founders: Dict[str, FounderInfo] = Field(
        ..., 
        description="Dictionary mapping founder names to their email and role",
        example={
            "John Doe": {"email": "john@example.com", "role": "CEO"},
            "Jane Smith": {"email": "jane@example.com", "role": "CTO"}
        }
    )
    
    # Investment Information (from UI)
    fund_id: int = Field(..., description="ID of the fund making the investment")
    amount_invested: Decimal = Field(..., description="Amount invested in the company")
    termsheet_sign_date: Optional[date] = Field(None, description="Date when term sheet was signed")
    funding_date: date = Field(..., description="Date when funding was completed")
    ec_sign_date: Optional[date] = Field(None, description="Date when employment contract was signed")
    latest_valuation: Optional[Decimal] = Field(None, description="Latest valuation of the company")
    valuation_date: Optional[date] = Field(None, description="Date of the latest valuation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "startup_brand": "Yinara",
                "sector": "Consumer",
                "pan": "AAACY1234D",
                "isin": "INE000123456",
                "product_description": "Luxury jewellery brand",
                "founders": {
                    "John Doe": {"email": "john@yinara.com", "role": "CEO"},
                    "Jane Smith": {"email": "jane@yinara.com", "role": "CTO"}
                },
                "fund_id": 12,
                "amount_invested": 15000000.00,
                "termsheet_sign_date": "2024-09-25",
                "funding_date": "2024-11-28",
                "ec_sign_date": "2024-10-03",
                "latest_valuation": 18000000.00,
                "valuation_date": "2025-03-31"
            }
        }
    )

# SHA Extracted Data Schema (for internal processing)
class SHAExtractedData(BaseModel):
    """Data extracted from SHA document (internal use only)"""
    execution_date: Optional[str] = None  # Will map to sha_sign_date
    company_name: Optional[str] = None
    company_address: Optional[str] = None

# Combined Onboard Response
class PortfolioOnboardResponse(BaseModel):
    company_id: int
    investment_id: int
    founder_ids: List[int]
    extracted_data: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

# List Response with pagination
class PortfolioCompanyListResponse(BaseModel):
    data: List[PortfolioCompanyResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)

class PortfolioFounderListResponse(BaseModel):
    data: List[PortfolioFounderResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)

class PortfolioInvestmentListResponse(BaseModel):
    data: List[PortfolioInvestmentResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)

class PortfolioDocumentListResponse(BaseModel):
    data: List[PortfolioDocumentResponse]
    total: int

    model_config = ConfigDict(from_attributes=True) 