"""
Service for processing Portfolio documents (SHA - Shareholders Agreement)
Handles document upload, text extraction, and data population for portfolio companies
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from datetime import datetime, date

from ..models.document import Document
from ..models.portfolio_document import PortfolioDocument
from ..models.portfolio_company import PortfolioCompany
from ..models.portfolio_founder import PortfolioFounder
from ..models.portfolio_investment import PortfolioInvestment
from ..utils.google_clients_gcp import drive_file_dump
from ..utils.pdf_extractor import extract_text_from_specific_pages, extract_text_from_pdf
from ..utils.llm import get_response_from_openai
from ..utils.constants import (
    DOCUMENT_PAGE_RANGES, DOCUMENT_TYPES, DOCUMENT_KEYWORDS, 
    SUPPORTED_MIME_TYPES
)
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from prompts.portfolio.sha_prompt import (
    sha_system_prompt, sha_user_prompt
)


class PortfolioDocumentProcessor:
    """Service class for processing Portfolio documents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def upload_document_to_drive(
        self, 
        file_path: str, 
        file_name: str, 
        mime_type: str,
        uploader_email: str,
        additional_shares: List[str] = None
    ) -> Dict[str, Any]:
        """
        Upload document to Google Drive
        
        Args:
            file_path: Local path to the file
            file_name: Name for the file on Drive
            mime_type: MIME type of the file
            uploader_email: Email of the uploader
            additional_shares: Additional emails to share with
            
        Returns:
            Dictionary with upload results and drive links
        """
        try:
            # Prepare additional shares list
            shares = []
            if additional_shares:
                for email in additional_shares:
                    shares.append({"email": email, "role": "reader"})
            
            # Upload to Drive
            result = drive_file_dump(
                file_path=file_path,
                file_name=file_name,
                mime_type=mime_type,
                share_with_email=uploader_email,
                additional_shares=shares
            )
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload to Drive: {str(e)}")
    
    def extract_document_text(self, file_path: str, document_type: str) -> str:
        """
        Extract text from document based on type and page ranges
        
        Args:
            file_path: Path to the PDF file
            document_type: Type of document (SHA)
            
        Returns:
            Extracted text content
        """
        try:
            # Get page ranges for the document type
            page_ranges = DOCUMENT_PAGE_RANGES.get(document_type, [])
            
            if not page_ranges:
                # Extract all pages if no specific range defined
                text, _, _ = extract_text_from_pdf(file_path)
            else:
                # Extract specific pages
                text, _, _ = extract_text_from_specific_pages(file_path, page_ranges)
            
            return text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")
    
    def process_sha_document(self, text: str) -> Dict[str, Any]:
        """
        Process SHA (Shareholders Agreement) using LLM
        
        Args:
            text: Extracted text from the document
            
        Returns:
            Dictionary with extracted fields
        """
        try:
            user_prompt = sha_user_prompt.format(sha_text=text)
            response = get_response_from_openai(
                system_prompt=sha_system_prompt,
                user_prompt=user_prompt,
                model_name="gpt-4.1-mini"
            )
            
            return json.loads(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process SHA: {str(e)}")
    
    def map_sha_fields_to_portfolio(self, sha_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map SHA fields to portfolio model fields
        
        Args:
            sha_data: Extracted data from SHA document
            
        Returns:
            Dictionary with portfolio model field mappings
        """
        portfolio_fields = {}
        
        # Company fields
        if sha_data.get("company_name"):
            portfolio_fields["company_name"] = sha_data["company_name"]
        
        if sha_data.get("company_address"):
            portfolio_fields["registered_address"] = sha_data["company_address"]
        
        # Investment fields - map execution_date to sha_sign_date
        if sha_data.get("execution_date"):
            try:
                # Parse the date string (assuming YYYY-MM-DD format)
                sha_sign_date = datetime.strptime(sha_data["execution_date"], "%Y-%m-%d").date()
                portfolio_fields["sha_sign_date"] = sha_sign_date
            except (ValueError, TypeError):
                # If parsing fails, store as string for manual review
                portfolio_fields["sha_sign_date_raw"] = sha_data["execution_date"]
        
        return portfolio_fields
    
    def calculate_funding_tat(self, termsheet_date: Optional[date], funding_date: Optional[date]) -> Optional[int]:
        """
        Calculate funding TAT (Turn Around Time) in days
        
        Args:
            termsheet_date: Date of term sheet signing
            funding_date: Date of funding
            
        Returns:
            Number of days between term sheet and funding, or None if either date is missing
        """
        if termsheet_date and funding_date:
            return (funding_date - termsheet_date).days
        return None
    
    def create_document_record(
        self,
        file_name: str,
        document_type: str,
        file_path: str,
        drive_result: Dict[str, Any],
        expiry_date: Optional[str] = None
    ) -> Document:
        """
        Create document record in database
        
        Args:
            file_name: Name of the document
            document_type: Type of document (SHA)
            file_path: Local file path
            drive_result: Result from Drive upload
            expiry_date: Optional expiry date
            
        Returns:
            Created Document instance
        """
        try:
            # Parse expiry date if provided
            parsed_expiry_date = None
            if expiry_date:
                try:
                    parsed_expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                except ValueError:
                    pass  # Ignore invalid date format
            
            # Get drive link from the correct path
            drive_link = drive_result.get("shared_links", {}).get("uploader")
            
            # Create document record
            document = Document(
                document_id=uuid.uuid4(),
                name=file_name,
                category=document_type,
                file_path=file_path,
                drive_file_id=drive_result.get("id"),
                drive_link=drive_link,  # Store the drive link
                expiry_date=parsed_expiry_date,
                status="Active"
            )
            
            self.db.add(document)
            self.db.flush()  # Get ID without committing
            
            return document
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create document record: {str(e)}")
    
    def create_portfolio_document_association(
        self,
        company_id: int,
        document_id: uuid.UUID,
        document_type: str,
        doc_link: Optional[str] = None
    ) -> PortfolioDocument:
        """
        Create portfolio-document association
        
        Args:
            company_id: Portfolio company ID
            document_id: Document ID
            document_type: Type of document
            doc_link: Optional document link
            
        Returns:
            Created PortfolioDocument instance
        """
        try:
            portfolio_doc = PortfolioDocument(
                company_id=company_id,
                document_id=document_id,
                document_type=document_type,
                doc_link=doc_link
            )
            
            self.db.add(portfolio_doc)
            self.db.flush()
            
            return portfolio_doc
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create portfolio document association: {str(e)}")
    
    def create_company_record(self, company_data: Dict[str, Any], extracted_data: Dict[str, Any]) -> PortfolioCompany:
        """
        Create portfolio company record
        
        Args:
            company_data: Company data from UI
            extracted_data: Extracted data from SHA
            
        Returns:
            Created PortfolioCompany instance
        """
        try:
            # Merge UI data with extracted data
            merged_data = {**company_data}
            
            # Add extracted fields with fallbacks
            if extracted_data.get("company_name"):
                merged_data["company_name"] = extracted_data["company_name"]
            else:
                # Fallback: Use startup_brand as company_name if SHA extraction failed
                merged_data["company_name"] = company_data.get("startup_brand", "Unknown Company")
            
            if extracted_data.get("registered_address"):
                merged_data["registered_address"] = extracted_data["registered_address"]
            else:
                # Fallback: Set a default placeholder if no address extracted
                merged_data["registered_address"] = "Address to be updated"
            
            # Create company record
            company = PortfolioCompany(**merged_data)
            
            self.db.add(company)
            self.db.flush()
            
            return company
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create company record: {str(e)}")
    
    def create_founder_records(
        self,
        company_id: int,
        founders_data: List[Dict[str, Any]],
        extracted_founder_names: List[str]
    ) -> List[PortfolioFounder]:
        """
        Create portfolio founder records (legacy method for backward compatibility)
        
        Args:
            company_id: Portfolio company ID
            founders_data: Founder data from UI (emails and roles)
            extracted_founder_names: Founder names extracted from SHA
            
        Returns:
            List of created PortfolioFounder instances
        """
        try:
            founder_records = []
            
            # Match founder names with emails/roles
            for i, founder_ui_data in enumerate(founders_data):
                founder_name = extracted_founder_names[i] if i < len(extracted_founder_names) else None
                
                founder = PortfolioFounder(
                    company_id=company_id,
                    founder_name=founder_name,
                    founder_email=founder_ui_data["founder_email"],
                    founder_role=founder_ui_data["founder_role"]
                )
                
                self.db.add(founder)
                self.db.flush()
                founder_records.append(founder)
            
            return founder_records
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create founder records: {str(e)}")
    
    def create_founder_records_from_dict(
        self,
        company_id: int,
        founders_dict: Dict[str, Any]
    ) -> List[PortfolioFounder]:
        """
        Create portfolio founder records from dict structure
        
        Args:
            company_id: Portfolio company ID
            founders_dict: Dict where key is founder name, value is FounderInfo object or dict with email and role
                          Example: {"John Doe": FounderInfo(email="john@example.com", role="CEO")}
                          Or: {"John Doe": {"email": "john@example.com", "role": "CEO"}}
            
        Returns:
            List of created PortfolioFounder instances
        """
        try:
            founder_records = []
            
            for founder_name, founder_info in founders_dict.items():
                # Handle both FounderInfo objects and plain dicts
                if hasattr(founder_info, 'email') and hasattr(founder_info, 'role'):
                    # FounderInfo object
                    email = founder_info.email
                    role = founder_info.role
                else:
                    # Plain dict
                    email = founder_info["email"]
                    role = founder_info["role"]
                
                founder = PortfolioFounder(
                    company_id=company_id,
                    founder_name=founder_name,
                    founder_email=email,
                    founder_role=role
                )
                
                self.db.add(founder)
                self.db.flush()
                founder_records.append(founder)
            
            return founder_records
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create founder records: {str(e)}")
    
    def create_investment_record(
        self,
        company_id: int,
        investment_data: Dict[str, Any],
        extracted_data: Dict[str, Any]
    ) -> PortfolioInvestment:
        """
        Create portfolio investment record
        
        Args:
            company_id: Portfolio company ID
            investment_data: Investment data from UI
            extracted_data: Extracted data from SHA
            
        Returns:
            Created PortfolioInvestment instance
        """
        try:
            # Merge UI data with extracted data
            merged_data = {**investment_data, "company_id": company_id}
            
            # Add extracted SHA sign date
            if extracted_data.get("sha_sign_date"):
                merged_data["sha_sign_date"] = extracted_data["sha_sign_date"]
            
            # Calculate funding TAT if both dates are available
            termsheet_date = merged_data.get("termsheet_sign_date")
            funding_date = merged_data.get("funding_date")
            
            if termsheet_date and funding_date:
                merged_data["funding_tat_days"] = self.calculate_funding_tat(termsheet_date, funding_date)
            
            # Create investment record
            investment = PortfolioInvestment(**merged_data)
            
            self.db.add(investment)
            self.db.flush()
            
            return investment
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create investment record: {str(e)}") 