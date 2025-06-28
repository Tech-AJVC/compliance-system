from pydantic import BaseModel, ConfigDict, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from .entity import EntityResponse

class SchemeStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class LegalStructure(str, Enum):
    TRUST = "Trust"
    COMPANY = "Company"
    LLP = "LLP"

class SchemeStructure(str, Enum):
    CLOSE_ENDED = "Close Ended"
    OPEN_ENDED = "Open Ended"

class CategorySubcategory(str, Enum):
    CATEGORY_I_AIF = "Category I AIF"
    CATEGORY_II_AIF = "Category II AIF"
    CATEGORY_III_AIF = "Category III AIF"

class FundBase(BaseModel):
    # Core fund details - all compulsory
    scheme_name: str
    scheme_status: SchemeStatus
    aif_name: str
    aif_pan: str
    aif_registration_no: str
    legal_structure: LegalStructure
    category_subcategory: CategorySubcategory
    scheme_structure_type: SchemeStructure
    
    # Fund management details - compulsory
    custodian_name: str
    rta_name: str
    compliance_officer_name: str
    compliance_officer_email: str
    compliance_officer_phone: str
    investment_officer_name: str
    investment_officer_designation: str
    investment_officer_pan: str
    investment_officer_din: str
    date_of_appointment: date
    
    # Scheme financial details - compulsory
    scheme_pan: str
    nav: int
    target_fund_size: Decimal
    
    # Important dates - compulsory
    date_final_draft_ppm: date
    date_sebi_ppm_comm: date
    date_launch_of_scheme: date
    date_initial_close: date
    date_final_close: date
    commitment_initial_close_cr: Decimal
    terms_end_date: date
    
    # Bank details - compulsory
    bank_name: str
    bank_ifsc: str
    bank_account_name: str
    bank_account_no: str
    bank_contact_person: str
    bank_contact_phone: str
    
    # Optional fields
    entity_type: Optional[str] = None
    entity_name: Optional[str] = None
    entity_pan: Optional[str] = None
    entity_email: Optional[str] = None
    entity_address: Optional[str] = None
    extension_permitted: Optional[bool] = None
    extended_end_date: Optional[date] = None
    greenshoe_option: Optional[Decimal] = None

    @validator('aif_pan', 'entity_pan', 'investment_officer_pan', 'scheme_pan')
    def validate_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError('PAN must be exactly 10 characters')
        return v.upper() if v else v

    @validator('bank_ifsc')
    def validate_ifsc(cls, v):
        if v and len(v) != 11:
            raise ValueError('IFSC must be exactly 11 characters')
        return v.upper() if v else v

    @validator('investment_officer_din')
    def validate_din(cls, v):
        if v and len(v) != 8:
            raise ValueError('DIN must be exactly 8 characters')
        return v

class FundCreate(FundBase):
    pass

class FundUpdate(BaseModel):
    scheme_name: Optional[str] = None
    scheme_status: Optional[SchemeStatus] = None
    aif_name: Optional[str] = None
    aif_pan: Optional[str] = None
    aif_registration_no: Optional[str] = None
    legal_structure: Optional[LegalStructure] = None
    category_subcategory: Optional[CategorySubcategory] = None
    scheme_structure_type: Optional[SchemeStructure] = None
    entity_type: Optional[str] = None
    entity_name: Optional[str] = None
    entity_pan: Optional[str] = None
    entity_email: Optional[str] = None
    entity_address: Optional[str] = None
    custodian_name: Optional[str] = None
    rta_name: Optional[str] = None
    compliance_officer_name: Optional[str] = None
    compliance_officer_email: Optional[str] = None
    compliance_officer_phone: Optional[str] = None
    investment_officer_name: Optional[str] = None
    investment_officer_designation: Optional[str] = None
    investment_officer_pan: Optional[str] = None
    investment_officer_din: Optional[str] = None
    date_of_appointment: Optional[date] = None
    scheme_pan: Optional[str] = None
    date_final_draft_ppm: Optional[date] = None
    date_sebi_ppm_comm: Optional[date] = None
    date_launch_of_scheme: Optional[date] = None
    date_initial_close: Optional[date] = None
    date_final_close: Optional[date] = None
    commitment_initial_close_cr: Optional[Decimal] = None
    terms_end_date: Optional[date] = None
    extension_permitted: Optional[bool] = None
    extended_end_date: Optional[date] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_contact_person: Optional[str] = None
    bank_contact_phone: Optional[str] = None
    nav: Optional[int] = None
    target_fund_size: Optional[Decimal] = None
    greenshoe_option: Optional[Decimal] = None

    @validator('aif_pan', 'entity_pan', 'investment_officer_pan', 'scheme_pan')
    def validate_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError('PAN must be exactly 10 characters')
        return v.upper() if v else v

    @validator('bank_ifsc')
    def validate_ifsc(cls, v):
        if v and len(v) != 11:
            raise ValueError('IFSC must be exactly 11 characters')
        return v.upper() if v else v

    @validator('investment_officer_din')
    def validate_din(cls, v):
        if v and len(v) != 8:
            raise ValueError('DIN must be exactly 8 characters')
        return v

class FundResponse(FundBase):
    fund_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FundSearch(BaseModel):
    fund_id: int
    scheme_name: str

    model_config = ConfigDict(from_attributes=True)

class FundDetailsSummary(BaseModel):
    """Comprehensive fund information for reporting"""
    fund_id: int
    scheme_details: dict
    aif_details: dict
    financial_info: dict
    important_dates: dict
    bank_details: dict

    model_config = ConfigDict(from_attributes=True)

class FundEntityBase(BaseModel):
    fund_id: int
    entity_id: int
    is_primary: bool = False

class FundEntityCreate(FundEntityBase):
    pass

class FundEntityResponse(FundEntityBase):
    fund_entity_id: int
    entity_details: Optional[EntityResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 