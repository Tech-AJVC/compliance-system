"""
Service for processing LP documents (KYC, Contribution Agreement, CML)
Handles document upload, text extraction, and data population
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from ..models.document import Document
from ..models.lp_document import LPDocument
from ..models.lp_details import LPDetails
from ..utils.google_clients_gcp import drive_file_dump
from ..utils.pdf_extractor import extract_text_from_specific_pages, extract_text_from_pdf
from ..utils.llm import get_response_from_openai
from ..utils.constants import (
    DOCUMENT_PAGE_RANGES, DOCUMENT_TYPES, DOCUMENT_KEYWORDS, 
    LP_STATUS, SUPPORTED_MIME_TYPES
)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from prompts.lp_details.contribution_agreement import (
    contribution_agg_sys_prompt, contribution_agg_user_prompt
)
from prompts.lp_details.cml_prompt import (
    cml_system_prompt, cml_user_prompt
)


class LPDocumentProcessor:
    """Service class for processing LP documents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def identify_document_type(self, filename: str, content: str = "") -> str:
        """
        Identify document type based on filename and content
        
        Args:
            filename: Name of the uploaded file
            content: Text content of the document (optional)
            
        Returns:
            Document type (KYC, CA, CML)
        """
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Check filename and content for keywords
        for doc_type, keywords in DOCUMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in filename_lower or keyword in content_lower:
                    return DOCUMENT_TYPES[doc_type]
        
        # Default fallback - try to guess from filename
        if "kyc" in filename_lower:
            return DOCUMENT_TYPES["KYC"]
        elif "contribution" in filename_lower or "agreement" in filename_lower:
            return DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"]
        elif "cml" in filename_lower or "master" in filename_lower:
            return DOCUMENT_TYPES["CML"]
        
        # If can't identify, default to KYC
        return DOCUMENT_TYPES["KYC"]
    
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
            document_type: Type of document (KYC, CA, CML)
            
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
    
    def process_contribution_agreement(self, text: str) -> Dict[str, Any]:
        """
        Process Contribution Agreement using LLM
        
        Args:
            text: Extracted text from the document
            
        Returns:
            Dictionary with extracted fields
        """
        try:
            user_prompt = contribution_agg_user_prompt.format(ca_text=text)
            response = get_response_from_openai(
                system_prompt=contribution_agg_sys_prompt,
                user_prompt=user_prompt,
                model_name="gpt-4o-mini"
            )
            
            return json.loads(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process CA: {str(e)}")
    
    def process_cml_document(self, text: str) -> Dict[str, Any]:
        """
        Process Client Master List using LLM
        
        Args:
            text: Extracted text from the document
            
        Returns:
            Dictionary with extracted fields
        """
        try:
            user_prompt = cml_user_prompt.format(cml_text=text)
            response = get_response_from_openai(
                system_prompt=cml_system_prompt,
                user_prompt=user_prompt,
                model_name="gpt-4o-mini"
            )
            
            return json.loads(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process CML: {str(e)}")
    
    def map_ca_fields_to_lp(self, ca_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Contribution Agreement fields to LP model fields
        
        Args:
            ca_data: Extracted data from Contribution Agreement
            
        Returns:
            Dictionary with LP model field mappings
        """
        lp_fields = {}
        
        # Direct mappings - using new separate field names
        if ca_data.get("name_of_contributor"):
            lp_fields["lp_name"] = ca_data["name_of_contributor"]
        
        if ca_data.get("address_of_contributor"):
            lp_fields["address"] = ca_data["address_of_contributor"]
        
        if ca_data.get("email_id"):
            lp_fields["email"] = ca_data["email_id"]
            lp_fields["email_for_drawdowns"] = ca_data["email_id"]  # Default same
        
        if ca_data.get("mobile_tel_no"):
            lp_fields["mobile_no"] = ca_data["mobile_tel_no"]
        
        if ca_data.get("amount_of_capital_commitment"):
            # Clean and convert commitment amount
            amount_str = str(ca_data["amount_of_capital_commitment"]).replace(",", "")
            try:
                lp_fields["commitment_amount"] = float(amount_str)
            except ValueError:
                pass
        
        if ca_data.get("date_of_agreement"):
            lp_fields["date_of_agreement"] = ca_data["date_of_agreement"]
        
        if ca_data.get("class_subclass_of_units"):
            lp_fields["class_of_shares"] = ca_data["class_subclass_of_units"]
            
            # ISIN mapping logic based on class of units
            class_of_units = ca_data["class_subclass_of_units"].upper()
            if "CLASS A" in class_of_units:
                lp_fields["isin"] = "INF1C8N22014"
            elif "CLASS B" in class_of_units:
                lp_fields["isin"] = "INF1C8N22022"
        
        # Handle nominee details
        nominee_details = ca_data.get("details_of_nominee", {})
        if isinstance(nominee_details, dict) and nominee_details.get("name"):
            lp_fields["nominee"] = nominee_details["name"]
        
        return lp_fields
    
    def map_cml_fields_to_lp(self, cml_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map CML fields to LP model fields
        
        Args:
            cml_data: Extracted data from CML
            
        Returns:
            Dictionary with LP model field mappings (only fields that exist in LP model)
        """
        lp_fields = {}
        
        # Direct mappings - only fields that exist in LP Details model
        if cml_data.get("pan"):
            lp_fields["pan"] = cml_data["pan"]
        
        if cml_data.get("dob"):
            lp_fields["dob"] = cml_data["dob"]
        
        if cml_data.get("doi"):
            lp_fields["doi"] = cml_data["doi"]
        
        if cml_data.get("client_id"):
            lp_fields["client_id"] = cml_data["client_id"]
        
        if cml_data.get("dpid"):
            lp_fields["dpid"] = cml_data["dpid"]
        
        if cml_data.get("citizenship"):
            lp_fields["citizenship"] = cml_data["citizenship"]
        
        if cml_data.get("type"):
            lp_fields["type"] = cml_data["type"]
        
        if cml_data.get("country"):
            lp_fields["geography"] = cml_data["country"]
        
        # Map depository field to CML field in LP_details
        if cml_data.get("depository"):
            lp_fields["cml"] = cml_data["depository"]
        
        # Note: Fields like dp, clid, first_holder_pan, client_type, 
        # number_of_foreign_investors are extracted from CML but not stored in LP model
        
        return lp_fields
    
    def update_lp_status(self, lp: LPDetails) -> str:
        """
        Update LP status based on attached documents
        
        Args:
            lp: LP Details instance
            
        Returns:
            New status
        """
        # Get associated documents
        lp_documents = self.db.query(LPDocument).filter(LPDocument.lp_id == lp.lp_id).all()
        
        # Check which document types are present
        doc_types = [doc.document_type for doc in lp_documents]
        
        has_kyc = DOCUMENT_TYPES["KYC"] in doc_types
        has_ca = DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"] in doc_types
        has_cml = DOCUMENT_TYPES["CML"] in doc_types
        
        # Determine status based on document availability
        if not has_kyc:
            return LP_STATUS["WAITING_FOR_KYC"]
        elif not has_ca or not has_cml:
            return LP_STATUS["CA_CML_PENDING"]
        else:
            return LP_STATUS["ACTIVE"]
    
    def create_document_record(
        self, 
        file_name: str, 
        document_type: str,
        file_path: str,
        drive_result: Dict[str, Any],
        expiry_date: Optional[str] = None
    ) -> Document:
        """
        Create a document record in the database
        
        Args:
            file_name: Name of the file
            document_type: Type of document
            file_path: Local file path
            drive_result: Result from Drive upload
            expiry_date: Expiry date for the document (optional)
            
        Returns:
            Created Document instance
        """
        # Map document type to category
        category_mapping = {
            DOCUMENT_TYPES["KYC"]: "KYC",
            DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"]: "Contribution Agreement",
            DOCUMENT_TYPES["CML"]: "CML"
        }
        
        document = Document(
            document_id=uuid.uuid4(),
            name=file_name,
            category=category_mapping.get(document_type, "CML"),
            file_path=file_path,
            drive_file_id=drive_result.get("id"),
            drive_link=drive_result.get("shared_links", {}).get("uploader"),
            status="Active"
        )
        
        # Set expiry date if provided
        if expiry_date:
            try:
                from datetime import datetime
                # Try to parse the date string
                parsed_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                document.expiry_date = parsed_date
            except ValueError:
                # If parsing fails, leave expiry_date as None
                pass
        
        self.db.add(document)
        self.db.flush()
        return document
    
    def create_lp_document_association(
        self, 
        lp_id: uuid.UUID, 
        document_id: uuid.UUID, 
        document_type: str
    ) -> LPDocument:
        """
        Create LP-Document association
        
        Args:
            lp_id: LP ID
            document_id: Document ID
            document_type: Type of document
            
        Returns:
            Created LPDocument instance
        """
        lp_document = LPDocument(
            lp_id=lp_id,
            document_id=document_id,
            document_type=document_type
        )
        
        self.db.add(lp_document)
        self.db.flush()
        return lp_document 