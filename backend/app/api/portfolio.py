from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
import os
import tempfile
import shutil
import json
from pathlib import Path
import logging
from app.database.base import get_db
from app.models.portfolio_company import PortfolioCompany
from app.models.portfolio_founder import PortfolioFounder
from app.models.portfolio_investment import PortfolioInvestment
from app.models.portfolio_document import PortfolioDocument
from app.models.document import Document
from app.schemas.portfolio import (
    PortfolioCompanyCreate, PortfolioCompanyUpdate, PortfolioCompanyResponse, PortfolioCompanyListResponse,
    PortfolioFounderCreate, PortfolioFounderUpdate, PortfolioFounderResponse, PortfolioFounderListResponse,
    PortfolioInvestmentCreate, PortfolioInvestmentUpdate, PortfolioInvestmentResponse, PortfolioInvestmentListResponse,
    PortfolioDocumentCreate, PortfolioDocumentUpdate, PortfolioDocumentResponse, PortfolioDocumentListResponse,
    PortfolioOnboardResponse, PortfolioOnboardingInput
)
from app.auth.security import get_current_user, check_role
from app.utils.audit import log_activity
from app.models.user import User
from app.services.portfolio_document_processor import PortfolioDocumentProcessor
from app.utils.constants import DOCUMENT_TYPES, SUPPORTED_MIME_TYPES
from datetime import datetime
from sqlalchemy import or_

router = APIRouter()

# Get logger for this module
logger = logging.getLogger(__name__)

# Custom dependency to parse JSON form field into Pydantic model
async def parse_portfolio_data(
    portfolio_data: str = Form(..., description="JSON string containing portfolio onboarding data")
) -> PortfolioOnboardingInput:
    """
    Dependency to parse and validate portfolio data from form field.
    """
    try:
        portfolio_data_dict = json.loads(portfolio_data)
        return PortfolioOnboardingInput(**portfolio_data_dict)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in portfolio data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid portfolio data: {str(e)}")

def validate_portfolio_uniqueness(db: Session, portfolio_data: PortfolioOnboardingInput, extracted_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Validate that portfolio company fields are unique before creation.
    Returns error dict if validation fails, None if all validations pass.
    """
    # Check startup_brand
    if portfolio_data.startup_brand:
        existing_company = db.query(PortfolioCompany).filter(
            PortfolioCompany.startup_brand == portfolio_data.startup_brand
        ).first()
        if existing_company:
            return {
                "error_type": "validation_error",
                "field": "startup_brand",
                "value": portfolio_data.startup_brand,
                "message": f"A portfolio company with startup brand '{portfolio_data.startup_brand}' already exists"
            }
    
    # Check company_name (from extracted fields)
    company_name = extracted_fields.get("company_name")
    if company_name:
        existing_company = db.query(PortfolioCompany).filter(
            PortfolioCompany.company_name == company_name
        ).first()
        if existing_company:
            return {
                "error_type": "validation_error",
                "field": "company_name",
                "value": company_name,
                "message": f"A portfolio company with company name '{company_name}' already exists"
            }
    
    # Check founder emails
    if portfolio_data.founders:
        for founder_name, founder_info in portfolio_data.founders.items():
            founder_email = founder_info.get("email")
            if founder_email:
                existing_founder = db.query(PortfolioFounder).filter(
                    PortfolioFounder.founder_email == founder_email
                ).first()
                if existing_founder:
                    return {
                        "error_type": "validation_error",
                        "field": "founder_email",
                        "value": founder_email,
                        "message": f"A founder with email '{founder_email}' already exists"
                    }
    
    return None

@router.post("/onboard", response_model=PortfolioOnboardResponse, status_code=status.HTTP_201_CREATED)
async def onboard_portfolio_company(
    # SHA Document upload
    sha_document: UploadFile = File(...),
    
    # Portfolio data parsed via dependency
    portfolio_data: PortfolioOnboardingInput = Depends(parse_portfolio_data),
    
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Combined portfolio company onboarding with SHA document processing.
    
    Uploads SHA document, extracts company information,
    and creates company, founder, and investment records atomically.
    
    The portfolio_data should be a JSON string containing all UI input fields.
    SHA-derived fields (company_name, registered_address, sha_sign_date) are extracted 
    automatically and combined with the provided data.
    
    Example portfolio_data JSON:
    {
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
    """
    logger.info(f"Starting portfolio onboarding for SHA document: {sha_document.filename}")
    logger.info(f"Parsed portfolio data for {len(portfolio_data.founders)} founders")
    
    # Check user permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        logger.warning(f"User {current_user.get('sub')} attempted portfolio creation without proper role")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have one of the required roles: Fund Manager, Compliance Officer, Fund Admin"
        )
    
    # Validate file type
    if not sha_document.filename.lower().endswith('.pdf'):
        logger.error(f"Invalid SHA file type: {sha_document.filename}")
        raise HTTPException(status_code=400, detail="SHA document must be a PDF")
    
    # Initialize processor
    processor = PortfolioDocumentProcessor(db)
    uploader_email = current_user.get("sub", "unknown@example.com")
    
    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save SHA document temporarily
            sha_path = os.path.join(temp_dir, f"sha_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            
            logger.info(f"Saving SHA document to: {sha_path}")
            with open(sha_path, "wb") as f:
                content = await sha_document.read()
                f.write(content)
            
            # Extract text from SHA document using specific pages
            logger.info("Extracting text from SHA document")
            sha_text = processor.extract_document_text(sha_path, DOCUMENT_TYPES["SHA"])
            logger.info(f"SHA text extracted, length: {len(sha_text)} characters")
            
            # Process SHA document with LLM
            logger.info("Processing SHA document with LLM")
            sha_data = processor.process_sha_document(sha_text)
            extracted_fields = processor.map_sha_fields_to_portfolio(sha_data)
            logger.info(f"SHA processing complete, extracted fields: {list(extracted_fields.keys())}")
            
            # Validate essential fields
            if not portfolio_data.startup_brand:
                logger.error("Missing startup_brand")
                raise HTTPException(status_code=400, detail="startup_brand is required")
            
            if not portfolio_data.founders:
                logger.error("Missing founders data")
                raise HTTPException(status_code=400, detail="At least one founder is required")
            
            if not portfolio_data.fund_id:
                logger.error("Missing fund_id")
                raise HTTPException(status_code=400, detail="fund_id is required")
            
            # Validate portfolio uniqueness before creation
            validation_error = validate_portfolio_uniqueness(db, portfolio_data, extracted_fields)
            if validation_error:
                logger.error(f"Portfolio validation failed: {validation_error}")
                raise HTTPException(status_code=400, detail=validation_error)
            
            # Prepare company data by combining UI input with SHA extracted fields
            company_data_dict = {
                "startup_brand": portfolio_data.startup_brand,
                "sector": portfolio_data.sector,
                "pan": portfolio_data.pan,
                "isin": portfolio_data.isin,
                "product_description": portfolio_data.product_description
            }
            
            # Prepare investment data from UI input
            investment_data_dict = {
                "fund_id": portfolio_data.fund_id,
                "amount_invested": portfolio_data.amount_invested,
                "funding_date": portfolio_data.funding_date,
                "termsheet_sign_date": portfolio_data.termsheet_sign_date,
                "ec_sign_date": portfolio_data.ec_sign_date,
                "latest_valuation": portfolio_data.latest_valuation,
                "valuation_date": portfolio_data.valuation_date
            }
            
            # Create company record (processor will merge with SHA extracted fields)
            logger.info("Creating portfolio company record")
            company = processor.create_company_record(company_data_dict, extracted_fields)
            logger.info(f"Company created: ID={company.company_id}, Name={company.startup_brand}")
            
            # Create founder records using the structured founders data
            logger.info("Creating founder records")
            founders = processor.create_founder_records_from_dict(
                company.company_id,
                portfolio_data.founders
            )
            logger.info(f"Created {len(founders)} founder records")
            
            # Create investment record (processor will merge with SHA extracted fields)
            logger.info("Creating investment record")
            investment = processor.create_investment_record(
                company.company_id,
                investment_data_dict,
                extracted_fields
            )
            logger.info(f"Investment created: ID={investment.investment_id}")
            
            # Upload SHA document to Drive and create document records
            logger.info("Uploading SHA document to Drive")
            drive_result = processor.upload_document_to_drive(
                file_path=sha_path,
                file_name=sha_document.filename,
                mime_type="application/pdf",
                uploader_email=uploader_email
            )
            
            # Get the drive link from the correct path in drive_result
            drive_link = drive_result.get("shared_links", {}).get("uploader")
            if not drive_link:
                logger.warning("Drive link not found in upload result")
            
            document = processor.create_document_record(
                file_name=sha_document.filename,
                document_type=DOCUMENT_TYPES["SHA"],
                file_path=sha_path,
                drive_result=drive_result
            )
            
            # Create portfolio-document association with drive link
            processor.create_portfolio_document_association(
                company.company_id,
                document.document_id,
                DOCUMENT_TYPES["SHA"],
                doc_link=drive_link  # Use the extracted drive link
            )
            
            # Commit all changes
            db.commit()
            logger.info("All changes committed successfully")
            
            # Log activity
            try:
                user_email = current_user.get("sub")
                user = db.query(User).filter(User.email == user_email).first()
                if user:
                    log_activity(
                        db=db,
                        activity="portfolio_company_onboarded",
                        user_id=user.user_id,
                        details=f"Onboarded portfolio company: {company.startup_brand}"
                    )
            except Exception as e:
                logger.error(f"Error logging activity: {str(e)}")
            
            # Prepare response
            return PortfolioOnboardResponse(
                company_id=company.company_id,
                investment_id=investment.investment_id,
                founder_ids=[f.founder_id for f in founders],
                extracted_data={
                    "company_name": extracted_fields.get("company_name"),
                    "registered_address": extracted_fields.get("registered_address"),
                    "sha_sign_date": str(extracted_fields.get("sha_sign_date")) if extracted_fields.get("sha_sign_date") else None,
                    "funding_tat_days": investment.funding_tat_days
                }
            )
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during portfolio onboarding: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error onboarding portfolio company: {str(e)}")

# Portfolio Companies Individual Management

@router.get("/", response_model=PortfolioCompanyListResponse)
async def get_portfolio_companies(
    skip: int = Query(0, description="Number of records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    db: Session = Depends(get_db)
):
    """Get all portfolio companies with pagination and optional filtering."""
    # Build query
    query = db.query(PortfolioCompany)
    
    # Apply filters
    if sector:
        query = query.filter(PortfolioCompany.sector == sector)
    
    # Get total count
    total = query.count()
    
    # Get paginated data
    companies = query.offset(skip).limit(limit).all()
    
    return PortfolioCompanyListResponse(data=companies, total=total)

@router.get("/search", response_model=PortfolioCompanyListResponse)
async def search_portfolio_companies(
    query: Optional[str] = Query(None, description="Search query for company name or startup brand"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    product_description: Optional[str] = Query(None, description="Search in product description"),
    registered_address: Optional[str] = Query(None, description="Search in registered address"),
    skip: int = Query(0, description="Number of records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Search and filter portfolio companies.
    
    Supports:
    - Full text search across company_name and startup_brand
    - Exact match filtering by sector
    - Partial text search in product_description and registered_address
    
    All search parameters are optional and can be combined.
    """
    # Start with base query
    base_query = db.query(PortfolioCompany)
    
    # Apply text search if query is provided
    if query:
        search_filter = or_(
            PortfolioCompany.company_name.ilike(f"%{query}%"),
            PortfolioCompany.startup_brand.ilike(f"%{query}%")
        )
        base_query = base_query.filter(search_filter)
    
    # Apply sector filter (exact match)
    if sector:
        base_query = base_query.filter(PortfolioCompany.sector == sector)
    
    # Apply product description search
    if product_description:
        base_query = base_query.filter(
            PortfolioCompany.product_description.ilike(f"%{product_description}%")
        )
    
    # Apply registered address search
    if registered_address:
        base_query = base_query.filter(
            PortfolioCompany.registered_address.ilike(f"%{registered_address}%")
        )
    
    # Get total count for pagination
    total = base_query.count()
    
    # Apply pagination
    companies = base_query.offset(skip).limit(limit).all()
    
    return PortfolioCompanyListResponse(data=companies, total=total)

# Portfolio Investments Management

@router.get("/investments", response_model=PortfolioInvestmentListResponse)
async def get_portfolio_investments(
    fund_id: Optional[int] = Query(None, description="Filter by fund ID"),
    skip: int = Query(0, description="Number of records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all portfolio investments with optional filtering."""
    query = db.query(PortfolioInvestment)
    
    # Apply filters
    if fund_id:
        query = query.filter(PortfolioInvestment.fund_id == fund_id)
    
    # Get total count
    total = query.count()
    
    # Get paginated data
    investments = query.offset(skip).limit(limit).all()
    
    return PortfolioInvestmentListResponse(data=investments, total=total)

@router.get("/investments/{investment_id}", response_model=PortfolioInvestmentResponse)
async def get_portfolio_investment(
    investment_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific portfolio investment by ID."""
    investment = db.query(PortfolioInvestment).filter(PortfolioInvestment.investment_id == investment_id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Portfolio investment not found")
    return investment

@router.put("/investments/{investment_id}", response_model=PortfolioInvestmentResponse)
async def update_portfolio_investment(
    investment_id: int,
    investment_data: PortfolioInvestmentUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing portfolio investment."""
    # Check permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    investment = db.query(PortfolioInvestment).filter(PortfolioInvestment.investment_id == investment_id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Portfolio investment not found")
    
    # Update investment data
    update_data = investment_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(investment, key, value)
    
    # Recalculate funding TAT if relevant dates are updated
    if 'termsheet_sign_date' in update_data or 'funding_date' in update_data:
        processor = PortfolioDocumentProcessor(db)
        investment.funding_tat_days = processor.calculate_funding_tat(
            investment.termsheet_sign_date,
            investment.funding_date
        )
    
    db.commit()
    db.refresh(investment)
    return investment

@router.delete("/investments/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a portfolio investment."""
    # Check permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    investment = db.query(PortfolioInvestment).filter(PortfolioInvestment.investment_id == investment_id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Portfolio investment not found")
    
    db.delete(investment)
    db.commit()
    return None

# Company-specific routes
@router.get("/{company_id}", response_model=PortfolioCompanyResponse)
async def get_portfolio_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific portfolio company by ID."""
    company = db.query(PortfolioCompany).filter(PortfolioCompany.company_id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Portfolio company not found")
    return company

@router.put("/{company_id}", response_model=PortfolioCompanyResponse)
async def update_portfolio_company(
    company_id: int,
    company_data: PortfolioCompanyUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing portfolio company."""
    # Check permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    company = db.query(PortfolioCompany).filter(PortfolioCompany.company_id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Portfolio company not found")
    
    # Update company data
    update_data = company_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)
    
    try:
        db.commit()
        db.refresh(company)
        return company
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Portfolio company with this name already exists")

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a portfolio company and all associated data."""
    # Check permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    company = db.query(PortfolioCompany).filter(PortfolioCompany.company_id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Portfolio company not found")
    
    company_name = company.startup_brand
    
    # Delete associated records in proper order
    # 1. Delete portfolio documents
    portfolio_docs = db.query(PortfolioDocument).filter(PortfolioDocument.company_id == company_id).all()
    for doc in portfolio_docs:
        db.delete(doc)
    
    # 2. Delete investments
    investments = db.query(PortfolioInvestment).filter(PortfolioInvestment.company_id == company_id).all()
    for investment in investments:
        db.delete(investment)
    
    # 3. Delete founders
    founders = db.query(PortfolioFounder).filter(PortfolioFounder.company_id == company_id).all()
    for founder in founders:
        db.delete(founder)
    
    # 4. Delete the company
    db.delete(company)
    db.commit()
    
    logger.info(f"Successfully deleted portfolio company: {company_name} and all associated records")
    return None

# Portfolio Founders Management

@router.get("/{company_id}/founders", response_model=PortfolioFounderListResponse)
async def get_company_founders(
    company_id: int,
    skip: int = Query(0, description="Number of records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all founders for a specific portfolio company."""
    # Check if company exists
    company = db.query(PortfolioCompany).filter(PortfolioCompany.company_id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Portfolio company not found")
    
    # Get founders with pagination
    query = db.query(PortfolioFounder).filter(PortfolioFounder.company_id == company_id)
    total = query.count()
    founders = query.offset(skip).limit(limit).all()
    
    return PortfolioFounderListResponse(data=founders, total=total)

@router.put("/founders/{founder_id}", response_model=PortfolioFounderResponse)
async def update_portfolio_founder(
    founder_id: int,
    founder_data: PortfolioFounderUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing portfolio founder."""
    # Check permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    founder = db.query(PortfolioFounder).filter(PortfolioFounder.founder_id == founder_id).first()
    if not founder:
        raise HTTPException(status_code=404, detail="Portfolio founder not found")
    
    # Update founder data
    update_data = founder_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(founder, key, value)
    
    try:
        db.commit()
        db.refresh(founder)
        return founder
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Founder with this email already exists")

@router.delete("/founders/{founder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_founder(
    founder_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a portfolio founder."""
    # Check permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    founder = db.query(PortfolioFounder).filter(PortfolioFounder.founder_id == founder_id).first()
    if not founder:
        raise HTTPException(status_code=404, detail="Portfolio founder not found")
    
    db.delete(founder)
    db.commit()
    return None

# Portfolio Documents Management

@router.get("/{company_id}/documents", response_model=PortfolioDocumentListResponse)
async def get_company_documents(
    company_id: int,
    skip: int = Query(0, description="Number of records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all documents for a specific portfolio company."""
    # Check if company exists
    company = db.query(PortfolioCompany).filter(PortfolioCompany.company_id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Portfolio company not found")
    
    # Get documents with pagination
    query = db.query(PortfolioDocument).filter(PortfolioDocument.company_id == company_id)
    total = query.count()
    documents = query.offset(skip).limit(limit).all()
    
    return PortfolioDocumentListResponse(data=documents, total=total)

@router.post("/{company_id}/documents", response_model=PortfolioDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio_document(
    company_id: int,
    document_data: PortfolioDocumentCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Link a document to a portfolio company."""
    # Check permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check if company exists
    company = db.query(PortfolioCompany).filter(PortfolioCompany.company_id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Portfolio company not found")
    
    # Check if document exists
    document = db.query(Document).filter(Document.document_id == document_data.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Create portfolio document association
    portfolio_doc = PortfolioDocument(
        company_id=company_id,
        document_id=document_data.document_id,
        document_type=document_data.document_type,
        doc_link=document_data.doc_link
    )
    
    db.add(portfolio_doc)
    db.commit()
    db.refresh(portfolio_doc)
    
    return portfolio_doc

@router.delete("/{company_id}/documents/{portfolio_document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_document(
    company_id: int,
    portfolio_document_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove a document association from a portfolio company."""
    # Check permissions
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Find the portfolio document
    portfolio_doc = db.query(PortfolioDocument).filter(
        PortfolioDocument.company_id == company_id,
        PortfolioDocument.portfolio_document_id == portfolio_document_id
    ).first()
    
    if not portfolio_doc:
        raise HTTPException(status_code=404, detail="Portfolio document association not found")
    
    db.delete(portfolio_doc)
    db.commit()
    return None 