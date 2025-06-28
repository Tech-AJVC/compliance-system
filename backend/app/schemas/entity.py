from pydantic import BaseModel, ConfigDict, validator, model_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class EntityType(str, Enum):
    MANAGER = "Manager"
    SPONSOR = "Sponsor"
    TRUST = "Trust"
    CUSTODIAN = "Custodian"
    RTA = "RTA"
    TRUSTEE = "Trustee"
    AUDITOR = "Auditor"
    MERCHANT_BANKER = "Merchant Banker"
    LEGAL_ADVISOR = "Legal Advisor"
    COMPLIANCE_OFFICER = "Compliance Officer"
    ACCOUNTANT = "Accountant"
    TAX = "Tax"

class EntityBase(BaseModel):
    entity_type: EntityType
    entity_pan: str
    entity_name: str
    entity_address: str
    entity_telephone: str
    entity_email: str
    entity_poc: str
    
    entity_registration_number: Optional[str] = None
    entity_tan: Optional[str] = None
    entity_date_of_incorporation: Optional[date] = None
    entity_gst_number: Optional[str] = None
    entity_poc_din: Optional[str] = None
    entity_poc_pan: Optional[str] = None

    @validator('entity_pan')
    def validate_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError('PAN must be exactly 10 characters')
        return v.upper() if v else v

    @validator('entity_poc_pan')
    def validate_poc_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError('POC PAN must be exactly 10 characters')
        return v.upper() if v else v

    @model_validator(mode='after')
    def validate_entity_requirements(self):
        entity_type = self.entity_type
        
        if not entity_type:
            return self
        
        registration_required = ['Sponsor', 'Manager', 'Merchant Banker', 'Auditor', 'RTA', 'Trustee', 'Trust']
        tan_required = ['Sponsor', 'Manager', 'Trust']
        incorporation_date_required = ['Sponsor', 'Manager', 'Trust']
        gst_required = ['Sponsor', 'Manager']
        poc_din_pan_required = ['Manager']
        
        if entity_type in registration_required and not self.entity_registration_number:
            raise ValueError(f'Registration Number is required for {entity_type}')
        
        if entity_type in tan_required and not self.entity_tan:
            raise ValueError(f'TAN Number is required for {entity_type}')
        
        if entity_type in incorporation_date_required and not self.entity_date_of_incorporation:
            raise ValueError(f'Date of Incorporation is required for {entity_type}')
        
        if entity_type in gst_required and not self.entity_gst_number:
            raise ValueError(f'GST Number is required for {entity_type}')
        
        if entity_type in poc_din_pan_required:
            if not self.entity_poc_din:
                raise ValueError(f'POC DIN Number is required for {entity_type}')
            if not self.entity_poc_pan:
                raise ValueError(f'POC PAN Number is required for {entity_type}')
        
        return self

class EntityCreate(EntityBase):
    pass

class EntityUpdate(BaseModel):
    entity_type: Optional[EntityType] = None
    entity_name: Optional[str] = None
    entity_pan: Optional[str] = None
    entity_address: Optional[str] = None
    entity_telephone: Optional[str] = None
    entity_email: Optional[str] = None
    entity_poc: Optional[str] = None
    entity_registration_number: Optional[str] = None
    entity_tan: Optional[str] = None
    entity_date_of_incorporation: Optional[date] = None
    entity_gst_number: Optional[str] = None
    entity_poc_din: Optional[str] = None
    entity_poc_pan: Optional[str] = None

    @validator('entity_pan')
    def validate_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError('PAN must be exactly 10 characters')
        return v.upper() if v else v

    @validator('entity_poc_pan')
    def validate_poc_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError('POC PAN must be exactly 10 characters')
        return v.upper() if v else v

class EntityResponse(EntityBase):
    entity_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EntitySearch(BaseModel):
    entity_id: int
    entity_name: Optional[str] = None
    entity_type: EntityType

    model_config = ConfigDict(from_attributes=True) 