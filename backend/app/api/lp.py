from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
import os
import tempfile
import shutil
from pathlib import Path
import logging
from app.database.base import get_db
from app.models.lp_details import LPDetails
from app.models.lp_drawdowns import LPDrawdown
from app.models.lp_document import LPDocument
from app.models.document import Document
from app.schemas.lp import (
    LPDetailsCreate, LPDetailsUpdate, LPDetailsResponse,
    LPDrawdownCreate, LPDrawdownUpdate, LPDrawdownResponse,
    LPWithDrawdowns, LPDocumentCreate, LPDocumentResponse,
    LPStatusUpdate, LPStatusResponse, DocumentUploadRequest,
    LPListResponse
)
from app.auth.security import get_current_user, check_role, get_password_hash
from app.utils.audit import log_activity
from app.models.user import User
import uuid
import csv
import io
import secrets
import string
from datetime import datetime, date
from pydantic import ValidationError, EmailStr, BaseModel
from fastapi.responses import JSONResponse
from app.utils.google_clients_gcp import gmail_send_email
from app.services.lp_document_processor import LPDocumentProcessor
from app.utils.constants import DOCUMENT_TYPES, SUPPORTED_MIME_TYPES
from app.models.compliance_records import ComplianceRecord

router = APIRouter()

# Get logger for this module
logger = logging.getLogger(__name__)

# LP Details Endpoints

@router.post("/bulk-upload/", status_code=status.HTTP_201_CREATED)
async def bulk_upload_lps(
        file: UploadFile = File(...),
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Upload multiple LP records in bulk using a CSV file.

    The CSV file should contain the following columns (headers required):
    - lp_name (required): Name of the LP
    - email (required): Email address of the LP
    - mobile_no: Mobile number
    - address: Physical address
    - pan: PAN number
    - dob: Date of birth (YYYY-MM-DD format)
    - doi: Date of incorporation (YYYY-MM-DD format)
    - gender: Gender
    - date_of_agreement: Agreement date (YYYY-MM-DD format)
    - commitment_amount: Commitment amount (numeric)
    - nominee: Nominee name
    - dpid: DP ID
    - client_id: Client ID
    - cml: CML
    - isin: ISIN
    - class_of_shares: Class of shares
    - citizenship: Citizenship
    - type: Type of LP
    - geography: Geography/Region

    Returns a summary of successful imports and any validation errors.
    """
    # Check if user has appropriate role
    # if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail=f"User does not have one of the required roles: Fund Manager, Compliance Officer, Fund Admin"
    #     )

    # Check file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a CSV file."
        )

    # Read and process the CSV file
    contents = await file.read()

    # Results tracking
    results = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "errors": [],
        "created_users": []  # Track created users and their passwords
    }

    try:
        # Parse CSV
        csv_text = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        # Validate CSV structure
        required_fields = ["lp_name", "email"]
        csv_fields = csv_reader.fieldnames

        if not csv_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or has no headers"
            )

        for field in required_fields:
            if field not in csv_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Required field '{field}' is missing from CSV headers"
                )

        # Process each row
        for i, row in enumerate(csv_reader):
            results["total"] += 1
            row_num = i + 2  # +2 because of 0-indexing and header row

            try:
                # Clean and transform data
                lp_data = {}

                # Required fields
                lp_data["lp_name"] = row["lp_name"].strip()

                # Handle multiple comma-separated email addresses
                if "email" in row and row["email"]:
                    emails = [email.strip() for email in row["email"].split(",")]
                    if not emails:
                        results["errors"].append({
                            "row": row_num,
                            "field": "email",
                            "value": row["email"],
                            "error": "Email is required"
                        })
                        raise ValueError("Missing required email")

                    # Use the first email as the primary email for the LP record
                    primary_email = emails[0]
                    lp_data["email"] = primary_email

                    # Store additional emails in the notes field if there are multiple
                    if len(emails) > 1:
                        additional_emails = ", ".join(emails[1:])
                        notes = f"Additional emails: {additional_emails}"

                        # If notes field already exists, append to it
                        if "notes" in lp_data and lp_data["notes"]:
                            lp_data["notes"] = f"{lp_data['notes']}\n{notes}"
                        else:
                            lp_data["notes"] = notes

                # Optional fields with appropriate type conversion
                if "mobile_no" in row and row["mobile_no"]:
                    lp_data["mobile_no"] = row["mobile_no"].strip()

                if "address" in row and row["address"]:
                    lp_data["address"] = row["address"].strip()

                if "nominee" in row and row["nominee"]:
                    lp_data["nominee"] = row["nominee"].strip()

                if "pan" in row and row["pan"]:
                    lp_data["pan"] = row["pan"].strip()

                # Handle date fields with multiple format support
                date_fields = ["dob", "doi", "date_of_agreement"]
                for field in date_fields:
                    if field in row and row[field] and str(row[field]).strip():
                        date_value = str(row[field]).strip()
                        parsed_date = None

                        # Try different date formats
                        formats_to_try = [
                            # ISO format
                            "%Y-%m-%d",
                            # Excel formats
                            "%d/%m/%Y",
                            "%d/%m/%y",  # DD/MM/YY format from Excel
                            # Other common formats
                            "%m/%d/%Y",
                            "%m/%d/%y",
                            "%d-%m-%Y",
                            "%d-%m-%y",
                            "%m-%d-%Y",
                            "%m-%d-%y",
                            "%d.%m.%Y",
                            "%d.%m.%y"
                        ]

                        for date_format in formats_to_try:
                            try:
                                parsed_date = datetime.strptime(date_value, date_format).date()
                                break
                            except ValueError:
                                continue

                        if parsed_date:
                            # For two-digit years, ensure proper century
                            current_year = datetime.now().year
                            if parsed_date.year < 100:  # Two-digit year detected
                                century_base = (current_year // 100) * 100
                                if parsed_date.year + century_base > current_year + 10:  # If date would be > 10 years in future
                                    # Assume previous century
                                    parsed_date = parsed_date.replace(year=parsed_date.year + century_base - 100)
                                else:
                                    # Use current century
                                    parsed_date = parsed_date.replace(year=parsed_date.year + century_base)

                            lp_data[field] = parsed_date
                        else:
                            results["errors"].append({
                                "row": row_num,
                                "field": field,
                                "value": date_value,
                                "error": f"Could not parse date for {field}. Try using format DD/MM/YYYY or YYYY-MM-DD."
                            })
                            raise ValueError(f"Invalid date format for {field}")

                # Handle numeric fields with Indian number format support
                if "commitment_amount" in row and row["commitment_amount"]:
                    try:
                        # Handle Indian number format (e.g., 1,00,00,000)
                        amount_str = str(row["commitment_amount"]).strip()

                        # First try direct conversion (for simple numbers without commas)
                        try:
                            lp_data["commitment_amount"] = float(amount_str)
                        except ValueError:
                            # Remove all commas and try again
                            clean_amount = amount_str.replace(',', '')
                            try:
                                lp_data["commitment_amount"] = float(clean_amount)
                            except ValueError:
                                # Handle special formats or non-numeric inputs
                                raise ValueError(f"Could not parse number: {amount_str}")

                    except ValueError as e:
                        results["errors"].append({
                            "row": row_num,
                            "field": "commitment_amount",
                            "value": row["commitment_amount"],
                            "error": f"Invalid commitment amount: {str(e)}"
                        })
                        raise ValueError("Invalid commitment_amount")

                # Handle boolean fields
                if "acknowledgement_of_ppm" in row and row["acknowledgement_of_ppm"]:
                    value = row["acknowledgement_of_ppm"].strip().lower()
                    if value in ["true", "yes", "1", "y"]:
                        lp_data["acknowledgement_of_ppm"] = True
                    elif value in ["false", "no", "0", "n"]:
                        lp_data["acknowledgement_of_ppm"] = False

                # Other string fields
                string_fields = ["gender", "dpid", "client_id", "cml", "isin",
                                 "class_of_shares", "citizenship", "type", "geography"]
                for field in string_fields:
                    if field in row and row[field]:
                        lp_data[field] = row[field].strip()

                # Validate with Pydantic model
                validated_data = LPDetailsCreate(**lp_data)

                # Check if LP with same email exists
                existing_lp = db.query(LPDetails).filter(LPDetails.email == validated_data.email).first()
                if existing_lp:
                    results["errors"].append({
                        "row": row_num,
                        "field": "email",
                        "value": validated_data.email,
                        "error": "LP with this email already exists"
                    })
                    results["failed"] += 1
                    continue

                # Check if LP with same PAN exists (if PAN provided)
                if validated_data.pan:
                    existing_lp_pan = db.query(LPDetails).filter(LPDetails.pan == validated_data.pan).first()
                    if existing_lp_pan:
                        results["errors"].append({
                            "row": row_num,
                            "field": "pan",
                            "value": validated_data.pan,
                            "error": "LP with this PAN already exists"
                        })
                        results["failed"] += 1
                        continue

                # Create new LP record
                new_lp = LPDetails(**validated_data.model_dump())
                db.add(new_lp)
                db.flush()  # Get ID without committing transaction

                # Create a corresponding user account with the same ID
                try:
                    # Generate a random password
                    password_chars = string.ascii_letters + string.digits + string.punctuation
                    random_password = ''.join(secrets.choice(password_chars) for _ in range(12))

                    # Create user directly without using the main.py endpoint
                    # First check if user already exists
                    existing_user = db.query(User).filter(User.email == new_lp.email).first()
                    if not existing_user:
                        # Hash the password
                        # hashed_password = get_password_hash(random_password)

                        # Create user with LP role and same ID
                        db_user = User(
                            user_id=new_lp.lp_id,
                            name=new_lp.lp_name,
                            email=new_lp.email,
                            role="LP",
                            password_hash=random_password,
                            mfa_enabled=False,
                            phone=new_lp.mobile_no
                        )
                        gmail_send_email("tech@ajuniorvc.com", db_user.email, "User Created Notification",
                                         f"A new user has been created:\n\n"
                                         f"Name: {new_lp.lp_name}\n"
                                         f"Email: {new_lp.email}\n"
                                         f"Role: LP\n"
                                         f"Password: {random_password}")

                        # Add user to the session (don't commit yet)
                        db.add(db_user)
                        db.flush()

                        print(f"Created user account for LP: {new_lp.lp_name} with ID: {new_lp.lp_id}")
                        print(f"Generated temporary password: {random_password}")

                        # TODO: Store the generated passwords for bulk email sending
                        # Could add to a list that's returned with the results
                except Exception as user_err:
                    # Log the error but don't fail the LP creation if user creation fails
                    print(f"Error creating user account for LP {new_lp.lp_name}: {str(user_err)}")

                # Count successful record
                results["successful"] += 1

            except ValidationError as e:
                error_details = e.errors()
                for error in error_details:
                    results["errors"].append({
                        "row": row_num,
                        "field": error["loc"][0],
                        "value": error.get("input", "Unknown"),
                        "error": error["msg"]
                    })
                results["failed"] += 1
            except ValueError:
                # Already logged in specific validation steps
                results["failed"] += 1
            except Exception as e:
                results["errors"].append({
                    "row": row_num,
                    "field": "unknown",
                    "value": "unknown",
                    "error": str(e)
                })
                results["failed"] += 1

        # Commit transaction if any records were successful
        if results["successful"] > 0:
            db.commit()

            # Log the activity
            try:
                # Get current user's ID from the database
                user_email = current_user.get("sub")
                user = db.query(User).filter(User.email == user_email).first()
                log_activity(
                    db=db,
                    activity="lp_bulk_upload",
                    user_id=user.user_id,
                    details=f"Bulk imported {results['successful']} LPs from CSV"
                )
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
        else:
            db.rollback()

        return results

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file encoding. Please use UTF-8 encoding."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the CSV file: {str(e)}"
        )


@router.post("/", response_model=LPDetailsResponse, status_code=status.HTTP_201_CREATED)
async def create_lp(
        # KYC Document fields
        kyc_file: UploadFile = File(...),
        kyc_category: str = Form(...),
        kyc_expiry_date: Optional[str] = Form(None),
        
        # CA Document fields
        ca_file: UploadFile = File(...),
        ca_category: str = Form(...),
        ca_expiry_date: Optional[str] = Form(None),
        
        # CML Document fields
        cml_file: UploadFile = File(...),
        cml_category: str = Form(...),
        cml_expiry_date: Optional[str] = Form(None),
        
        fund_id: Optional[int] = Form(None),
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Create a new LP (Limited Partner) record by extracting data from uploaded documents.
    Requires KYC, CA (Contribution Agreement), and CML (Client Master List) documents.
    
    Each document type requires:
    - file: The document file to upload
    - category: Document category (should match the document type)
    - expiry_date: Optional expiry date for the document
    
    The file name will be used as the document name.
    """
    logger.info(f"Starting LP creation process for files: KYC={kyc_file.filename}, CA={ca_file.filename}, CML={cml_file.filename}")
    
    # Check if user has appropriate role
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        logger.warning(f"User {current_user.get('sub')} attempted LP creation without proper role: {current_user.get('role')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have one of the required roles: Fund Manager, Compliance Officer, Fund Admin"
        )

    # Initialize processor
    processor = LPDocumentProcessor(db)
    uploader_email = current_user.get("sub", "unknown@example.com")
    
    # Generate a UUID to use for both LP and User
    lp_user_id = uuid.uuid4()
    logger.info(f"Generated LP/User ID: {lp_user_id}")
    
    # Validate file types
    if not kyc_file.filename.lower().endswith('.pdf'):
        logger.error(f"Invalid KYC file type: {kyc_file.filename}")
        raise HTTPException(status_code=400, detail="KYC file must be a PDF")
    if not ca_file.filename.lower().endswith('.pdf'):
        logger.error(f"Invalid CA file type: {ca_file.filename}")
        raise HTTPException(status_code=400, detail="CA file must be a PDF")
    if not cml_file.filename.lower().endswith('.pdf'):
        logger.error(f"Invalid CML file type: {cml_file.filename}")
        raise HTTPException(status_code=400, detail="CML file must be a PDF")

    logger.info("All file type validations passed")

    # Validate categories match expected document types
    if kyc_category.lower() != "kyc":
        logger.error(f"Invalid KYC category: {kyc_category}")
        raise HTTPException(status_code=400, detail="KYC category must be 'KYC'")
    if ca_category.lower() != "contribution_agreement":
        logger.error(f"Invalid CA category: {ca_category}")
        raise HTTPException(status_code=400, detail="CA category must be 'Contribution_Agreement'")
    if cml_category.lower() != "cml":
        logger.error(f"Invalid CML category: {cml_category}")
        raise HTTPException(status_code=400, detail="CML category must be 'CML'")

    logger.info("All category validations passed")

    try:
        # Create temporary directory for processing
        import tempfile
        import os
        from datetime import datetime
        
        logger.info("Creating temporary directory for document processing")
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files temporarily
            kyc_path = os.path.join(temp_dir, f"kyc_{lp_user_id}.pdf")
            ca_path = os.path.join(temp_dir, f"ca_{lp_user_id}.pdf")
            cml_path = os.path.join(temp_dir, f"cml_{lp_user_id}.pdf")
            
            logger.info(f"Saving temporary files: KYC={kyc_path}, CA={ca_path}, CML={cml_path}")
            
            # Write files to temporary paths
            with open(kyc_path, "wb") as f:
                content = await kyc_file.read()
                f.write(content)
            
            with open(ca_path, "wb") as f:
                content = await ca_file.read()
                f.write(content)
            
            with open(cml_path, "wb") as f:
                content = await cml_file.read()
                f.write(content)
            
            logger.info("All files saved successfully, starting document processing")
            
            # Extract data from CA document
            logger.info("Extracting text from CA document")
            ca_text = processor.extract_document_text(ca_path, DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"])
            logger.info(f"CA text extracted, length: {len(ca_text)} characters")
            
            logger.info("Processing CA document with LLM")
            ca_data = processor.process_contribution_agreement(ca_text)
            ca_fields = processor.map_ca_fields_to_lp(ca_data)
            logger.info(f"CA processing complete, extracted fields: {list(ca_fields.keys())}")
            
            # Extract data from CML document
            logger.info("Extracting text from CML document")
            cml_text = processor.extract_document_text(cml_path, DOCUMENT_TYPES["CML"])
            logger.info(f"CML text extracted, length: {len(cml_text)} characters")
            
            logger.info("Processing CML document with LLM")
            cml_data = processor.process_cml_document(cml_text)
            cml_fields = processor.map_cml_fields_to_lp(cml_data)
            logger.info(f"CML processing complete, extracted fields: {list(cml_fields.keys())}")
            
            # Combine data from both documents
            lp_data = {**ca_fields, **cml_fields}
            logger.info(f"Combined LP data: {lp_data}")
            
            # Validate that we have essential fields
            if not lp_data.get("lp_name"):
                logger.error("Could not extract LP name from CA document")
                raise HTTPException(status_code=400, detail="Could not extract LP name from CA document")
            if not lp_data.get("email"):
                logger.error("Could not extract email from CA document")
                raise HTTPException(status_code=400, detail="Could not extract email from CA document")
            
            logger.info(f"Essential fields validated: LP Name={lp_data.get('lp_name')}, Email={lp_data.get('email')}")
            
            # Add fund_id if provided
            if fund_id:
                lp_data["fund_id"] = fund_id
                logger.info(f"Fund ID added: {fund_id}")
            
            # Set initial status to Active since all required documents (KYC, CA, CML) are provided
            lp_data["status"] = "Active"
            logger.info("Initial status set to 'Active' - all required documents provided")
            
            # Parse date fields if they exist
            if lp_data.get("dob") and isinstance(lp_data["dob"], str):
                try:
                    lp_data["dob"] = datetime.strptime(lp_data["dob"], "%Y-%m-%d").date()
                    logger.info(f"DOB parsed successfully: {lp_data['dob']}")
                except ValueError:
                    logger.warning(f"Could not parse DOB: {lp_data['dob']}")
                    pass
            
            if lp_data.get("doi") and isinstance(lp_data["doi"], str):
                try:
                    lp_data["doi"] = datetime.strptime(lp_data["doi"], "%Y-%m-%d").date()
                    logger.info(f"DOI parsed successfully: {lp_data['doi']}")
                except ValueError:
                    logger.warning(f"Could not parse DOI: {lp_data['doi']}")
                    pass
            
            if lp_data.get("date_of_agreement") and isinstance(lp_data["date_of_agreement"], str):
                try:
                    lp_data["date_of_agreement"] = datetime.strptime(lp_data["date_of_agreement"], "%Y-%m-%d").date()
                    logger.info(f"Date of agreement parsed successfully: {lp_data['date_of_agreement']}")
                except ValueError:
                    logger.warning(f"Could not parse date of agreement: {lp_data['date_of_agreement']}")
                    pass
            
            # Create new LP record with the generated UUID
            logger.info("Creating new LP record in database")
            new_lp = LPDetails(lp_id=lp_user_id, **{k: v for k, v in lp_data.items() if v is not None})
            
            # Add and commit the LP record
            db.add(new_lp)
            db.commit()
            db.refresh(new_lp)
            print(f"Created LP record for LP: {new_lp.lp_name} with ID: {new_lp.lp_id} with details {lp_data}")
            logger.info(f"LP record created successfully: ID={new_lp.lp_id}, Name={new_lp.lp_name}")
            
            # Create a corresponding user account with the same ID
            logger.info("Starting user account creation")
            try:
                # Generate a random password
                password_chars = string.ascii_letters + string.digits + string.punctuation
                random_password = ''.join(secrets.choice(password_chars) for _ in range(12))
                logger.info("Random password generated for user account")

                # Create user directly without using the main.py endpoint
                # First check if user already exists
                existing_user = db.query(User).filter(User.email == new_lp.email).first()
                if not existing_user:
                    logger.info(f"Creating new user account for email: {new_lp.email}")
                    # Create user with LP role and same ID
                    db_user = User(
                        user_id=new_lp.lp_id,
                        name=new_lp.lp_name,
                        email=new_lp.email,
                        role="LP",
                        password_hash=random_password,
                        mfa_enabled=False,
                        phone=new_lp.mobile_no
                    )
                    
                    # Add and commit the user record
                    db.add(db_user)
                    db.commit()
                    db.refresh(db_user)
                    
                    print(f"Created user account for LP: {new_lp.lp_name} with ID: {new_lp.lp_id}")
                    print(f"Generated temporary password: {random_password}")
                    logger.info(f"User account created successfully: ID={db_user.user_id}, Email={db_user.email}")
                    
                    # Send notification email
                    try:
                        logger.info("Sending welcome email to new user")
                        # gmail_send_email("tech@ajuniorvc.com", db_user.email, "User Created Notification",
                        #                  f"A new user has been created:\n\n"
                        #                  f"Name: {new_lp.lp_name}\n"
                        #                  f"Email: {new_lp.email}\n"
                        #                  f"Role: LP\n"
                        #                  f"Password: {random_password}")
                        logger.info("Welcome email sent successfully")
                    except Exception as email_err:
                        logger.error(f"Error sending welcome email: {str(email_err)}")
                        print(f"Error sending welcome email: {str(email_err)}")
                else:
                    logger.info(f"User already exists for email: {new_lp.email}")

            except Exception as user_err:
                # Log the error but don't fail the LP creation if user creation fails
                logger.error(f"Error creating user account for LP: {str(user_err)}")
                print(f"Error creating user account for LP: {str(user_err)}")

            # Process and upload documents
            logger.info("Starting document processing and upload")
            try:
                # Process KYC document
                logger.info("Processing KYC document")
                kyc_drive_result = processor.upload_document_to_drive(
                    file_path=kyc_path,
                    file_name=kyc_file.filename,
                    mime_type="application/pdf",
                    uploader_email=uploader_email
                )
                logger.info(f"KYC document uploaded to Drive: {kyc_drive_result.get('id')}")
                
                kyc_document = processor.create_document_record(
                    file_name=kyc_file.filename,
                    document_type=DOCUMENT_TYPES["KYC"],
                    file_path=kyc_path,
                    drive_result=kyc_drive_result,
                    expiry_date=kyc_expiry_date
                )
                logger.info(f"KYC document record created: {kyc_document.document_id}")
                
                processor.create_lp_document_association(new_lp.lp_id, kyc_document.document_id, DOCUMENT_TYPES["KYC"])
                logger.info("KYC document association created")

                # Process CA document
                logger.info("Processing CA document")
                ca_drive_result = processor.upload_document_to_drive(
                    file_path=ca_path,
                    file_name=ca_file.filename,
                    mime_type="application/pdf",
                    uploader_email=uploader_email
                )
                logger.info(f"CA document uploaded to Drive: {ca_drive_result.get('id')}")
                
                ca_document = processor.create_document_record(
                    file_name=ca_file.filename,
                    document_type=DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"],
                    file_path=ca_path,
                    drive_result=ca_drive_result,
                    expiry_date=ca_expiry_date
                )
                logger.info(f"CA document record created: {ca_document.document_id}")
                
                processor.create_lp_document_association(new_lp.lp_id, ca_document.document_id, DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"])
                logger.info("CA document association created")

                # Process CML document
                logger.info("Processing CML document")
                cml_drive_result = processor.upload_document_to_drive(
                    file_path=cml_path,
                    file_name=cml_file.filename,
                    mime_type="application/pdf",
                    uploader_email=uploader_email
                )
                logger.info(f"CML document uploaded to Drive: {cml_drive_result.get('id')}")
                
                cml_document = processor.create_document_record(
                    file_name=cml_file.filename,
                    document_type=DOCUMENT_TYPES["CML"],
                    file_path=cml_path,
                    drive_result=cml_drive_result,
                    expiry_date=cml_expiry_date
                )
                logger.info(f"CML document record created: {cml_document.document_id}")
                
                processor.create_lp_document_association(new_lp.lp_id, cml_document.document_id, DOCUMENT_TYPES["CML"])
                logger.info("CML document association created")

                # Mark KYC status as Done
                new_lp.kyc_status = "Done"
                logger.info("KYC status marked as 'Done'")
                
                # Update LP status
                new_lp.status = processor.update_lp_status(new_lp)
                logger.info(f"LP status updated to: {new_lp.status}")
                
                # Commit all changes
                db.commit()
                logger.info("All document processing changes committed to database")
                
            except Exception as e:
                # If document processing fails, cleanup LP record
                logger.error(f"Document processing failed: {str(e)}")
                db.delete(new_lp)
                db.commit()
                logger.info("LP record deleted due to document processing failure")
                raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")
            
            # Log the activity
            try:
                user_email = current_user.get("sub")
                user = db.query(User).filter(User.email == user_email).first()
                if user:
                    log_activity(
                        db=db,
                        activity="lp_created",
                        user_id=user.user_id,
                        details=f"Created LP: {new_lp.lp_name}"
                    )
                    logger.info("Activity logged successfully")
            except Exception as e:
                logger.error(f"Error logging activity: {str(e)}")
                print(f"Error logging activity: {str(e)}")
                # Continue even if logging fails

            # Refresh LP to get updated status
            db.refresh(new_lp)
            logger.info(f"LP creation process completed successfully for: {new_lp.lp_name} (ID: {new_lp.lp_id})")
            return new_lp
    
    except HTTPException:
        # Re-raise HTTP exceptions
        logger.error("HTTP exception occurred during LP creation")
        raise
    except IntegrityError:
        logger.error("Database integrity error during LP creation")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LP with this email or PAN already exists"
        )
    except Exception as e:
        # Handle any other exceptions
        logger.error(f"Unexpected error during LP creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating LP from documents: {str(e)}"
        )


@router.get("/", response_model=LPListResponse)
async def get_all_lps(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Get all LP records with pagination and total count.
    """
    # Get total count
    total = db.query(LPDetails).count()
    
    # Get paginated data
    lps = db.query(LPDetails).offset(skip).limit(limit).all()
    
    return LPListResponse(data=lps, total=total)


@router.get("/search/", response_model=List[LPDetailsResponse])
async def search_lps_by_name(
        name: str = Query(..., description="Name to search for (case-insensitive partial match)"),
        skip: int = Query(0, description="Number of records to skip for pagination"),
        limit: int = Query(100, description="Maximum number of records to return"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Search for LP records by name using case-insensitive partial matching.

    - Search is performed using ILIKE for partial matches
    - Results are paginated
    - Requires authentication
    """
    # Check if user has appropriate role
    check_role(["Fund Manager", "Compliance Officer", "Fund Admin"])

    # Search for LPs with name matching the search term (case-insensitive)
    lps = db.query(LPDetails).filter(
        LPDetails.lp_name.ilike(f"%{name}%")
    ).offset(skip).limit(limit).all()

    # Create audit log for the search operation
    try:
        log_activity(
            db=db,
            activity="lp_search",
            user_id=uuid.UUID(current_user.get("sub", "00000000-0000-0000-0000-000000000000")),
            details=f"Searched for LPs with name containing '{name}'"
        )
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        # Continue even if logging fails

    return lps


@router.get("/{lp_id}", response_model=LPWithDrawdowns)
async def get_lp(
        lp_id: uuid.UUID,
        db: Session = Depends(get_db)
):
    """
    Get a specific LP record by ID, including their drawdowns.
    """
    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if not lp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LP not found"
        )
    return lp


@router.put("/{lp_id}", response_model=LPDetailsResponse)
async def update_lp(
        lp_id: uuid.UUID,
        lp_data: LPDetailsUpdate,
        db: Session = Depends(get_db)
):
    """
    Update an existing LP record.
    """
    # Check if user has appropriate role
    check_role(["Fund Manager", "Compliance Officer", "Fund Admin"])

    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if not lp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LP not found"
        )

    # Update LP data
    update_data = lp_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lp, key, value)

    try:
        db.commit()
        db.refresh(lp)

        # Log the activity
        try:
            # Print the current_user dictionary to see what keys are available
            print(f"Current user: {await get_current_user()}")

            log_activity(
                db=db,
                activity="lp_updated",
                user_id=uuid.UUID(await get_current_user().get("sub", "00000000-0000-0000-0000-000000000000")),
                details=f"Updated LP: {lp.lp_name}"
            )
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
            # Continue even if logging fails

        return lp
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LP with this email or PAN already exists"
        )

@router.delete("/{lp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lp(
        lp_id: uuid.UUID,
        db: Session = Depends(get_db)
):
    """
    Delete an LP record and all associated data.
    """

    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if not lp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LP not found"
        )

    # Log before deletion
    lp_name = lp.lp_name

    # Delete all associated records first to avoid foreign key constraint violations
    
    # 1. Delete LP Documents
    lp_documents = db.query(LPDocument).filter(LPDocument.lp_id == lp_id).all()
    for lp_doc in lp_documents:
        db.delete(lp_doc)
    
    # 2. Delete LP Drawdowns
    lp_drawdowns = db.query(LPDrawdown).filter(LPDrawdown.lp_id == lp_id).all()
    for drawdown in lp_drawdowns:
        db.delete(drawdown)
    
    # 3. Delete Compliance Records
    compliance_records = db.query(ComplianceRecord).filter(ComplianceRecord.lp_id == lp_id).all()
    for record in compliance_records:
        db.delete(record)
    
    # 4. Delete User account if it exists with the same ID
    user = db.query(User).filter(User.user_id == lp_id).first()
    if user:
        db.delete(user)
    
    # 5. Finally delete the LP record itself
    db.delete(lp)
    db.commit()

    # Skip activity logging for this endpoint since authentication was removed
    print(f"Successfully deleted LP: {lp_name} and all associated records")

    return None


# LP Drawdown Endpoints
@router.post("/drawdowns", response_model=LPDrawdownResponse, status_code=status.HTTP_201_CREATED)
async def create_drawdown(
        drawdown_data: LPDrawdownCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new drawdown record for an LP.
    """
    # Check if user has appropriate role
    check_role(["Fund Manager", "Fund Admin"])

    # Check if LP exists
    lp = db.query(LPDetails).filter(LPDetails.lp_id == drawdown_data.lp_id).first()
    if not lp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LP not found"
        )

    # Create new drawdown
    new_drawdown = LPDrawdown(**drawdown_data.model_dump())

    db.add(new_drawdown)
    db.commit()
    db.refresh(new_drawdown)

    # Log the activity
    try:
        user = await get_current_user()
        # Print the current_user dictionary to see what keys are available
        print(f"Current user: {user}")

        log_activity(
            db=db,
            activity="drawdown_created",
            user_id=uuid.UUID(user.get("sub", "00000000-0000-0000-0000-000000000000")),
            details=f"Created drawdown for LP: {lp.lp_name}, Amount: {new_drawdown.amount}"
        )
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        # Continue even if logging fails

    return new_drawdown


@router.get("/drawdowns/list", response_model=List[LPDrawdownResponse])
async def get_all_drawdowns(
        lp_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Get all drawdown records with optional filtering by LP.
    """
    print("Getting drawdowns with lp_id:", lp_id)
    query = db.query(LPDrawdown)

    if lp_id:
        query = query.filter(LPDrawdown.lp_id == lp_id)

    drawdowns = query.offset(skip).limit(limit).all()
    return drawdowns


@router.get("/drawdowns/{drawdown_id}", response_model=LPDrawdownResponse)
async def get_drawdown(
        drawdown_id: uuid.UUID,
        db: Session = Depends(get_db)
):
    """
    Get a specific drawdown record by ID.
    """
    drawdown = db.query(LPDrawdown).filter(LPDrawdown.drawdown_id == drawdown_id).first()
    if not drawdown:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drawdown not found"
        )
    return drawdown


@router.put("/drawdowns/{drawdown_id}", response_model=LPDrawdownResponse)
async def update_drawdown(
        drawdown_id: uuid.UUID,
        drawdown_data: LPDrawdownUpdate,
        db: Session = Depends(get_db)
):
    """
    Update an existing drawdown record.
    """
    # Check if user has appropriate role
    check_role(["Fund Manager", "Fund Admin"])

    drawdown = db.query(LPDrawdown).filter(LPDrawdown.drawdown_id == drawdown_id).first()
    if not drawdown:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drawdown not found"
        )

    # Update drawdown data
    update_data = drawdown_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(drawdown, key, value)

    db.commit()
    db.refresh(drawdown)

    # Log the activity
    try:
        # Print the current_user dictionary to see what keys are available
        current_user = await get_current_user()
        print(f"Current user: {current_user}")

        log_activity(
            db=db,
            activity="drawdown_updated",
            user_id=uuid.UUID(current_user.get("sub", "00000000-0000-0000-0000-000000000000")),
            details=f"Updated drawdown: {drawdown_id}"
        )
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        # Continue even if logging fails

    return drawdown


@router.delete("/drawdowns/{drawdown_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drawdown(
        drawdown_id: uuid.UUID,
        db: Session = Depends(get_db)
):
    """
    Delete a drawdown record.
    """
    # Check if user has appropriate role
    check_role(["Fund Manager", "Fund Admin"])

    drawdown = db.query(LPDrawdown).filter(LPDrawdown.drawdown_id == drawdown_id).first()
    if not drawdown:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drawdown not found"
        )

    db.delete(drawdown)
    db.commit()

    # Log the activity
    try:
        # Print the current_user dictionary to see what keys are available
        current_user = await get_current_user()
        print(f"Current user: {current_user}")

        log_activity(
            db=db,
            activity="drawdown_deleted",
            user_id=uuid.UUID(current_user.get("sub", "00000000-0000-0000-0000-000000000000")),
            details=f"Deleted drawdown: {drawdown_id}"
        )
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        # Continue even if logging fails

    return None

# Helper function for document processing
async def process_lp_document(
    file: UploadFile, 
    lp_id: uuid.UUID, 
    doc_type: str, 
    uploader_email: str,
    processor: LPDocumentProcessor,
    expiry_date: Optional[str] = None
):
    """Process and upload a single LP document"""
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name

    try:
        # Get file extension and MIME type
        file_ext = Path(file.filename).suffix.lower()
        mime_type = SUPPORTED_MIME_TYPES.get(file_ext, "application/octet-stream")

        # Upload to Drive
        drive_result = processor.upload_document_to_drive(
            file_path=tmp_path,
            file_name=file.filename,
            mime_type=mime_type,
            uploader_email=uploader_email
        )

        # Create document record
        document = processor.create_document_record(
            file_name=file.filename,
            document_type=doc_type,
            file_path=tmp_path,
            drive_result=drive_result,
            expiry_date=expiry_date
        )

        # Create LP-Document association
        processor.create_lp_document_association(lp_id, document.document_id, doc_type)

        # Process document content for CA and CML
        if doc_type in [DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"], DOCUMENT_TYPES["CML"]]:
            if file_ext == ".pdf":
                text = processor.extract_document_text(tmp_path, doc_type)
                
                # Extract and update LP fields
                if doc_type == DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"]:
                    ca_data = processor.process_contribution_agreement(text)
                    lp_fields = processor.map_ca_fields_to_lp(ca_data)
                elif doc_type == DOCUMENT_TYPES["CML"]:
                    cml_data = processor.process_cml_document(text)
                    lp_fields = processor.map_cml_fields_to_lp(cml_data)
                
                # Update LP with extracted fields
                lp = processor.db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
                if lp and lp_fields:
                    for key, value in lp_fields.items():
                        if hasattr(lp, key) and value:
                            setattr(lp, key, value)

        # Mark KYC status as Done if KYC document uploaded
        if doc_type == DOCUMENT_TYPES["KYC"]:
            lp = processor.db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
            if lp:
                lp.kyc_status = "Done"

    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# LP Documents endpoints
@router.get("/{lp_id}/documents", response_model=List[LPDocumentResponse])
async def get_lp_documents(
        lp_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """Get all documents for a specific LP"""
    # Check if LP exists
    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="LP not found")

    # Get LP documents with document details
    lp_documents = db.query(LPDocument).filter(LPDocument.lp_id == lp_id).all()
    
    result = []
    for lp_doc in lp_documents:
        document = db.query(Document).filter(Document.document_id == lp_doc.document_id).first()
        doc_response = LPDocumentResponse(
            lp_document_id=lp_doc.lp_document_id,
            lp_id=lp_doc.lp_id,
            document_id=lp_doc.document_id,
            document_type=lp_doc.document_type,
            created_at=lp_doc.created_at,
            document_details={
                "name": document.name if document else None,
                "drive_link": document.drive_link if document else None,
                "status": document.status if document else None,
                "expiry_date": document.expiry_date if document else None
            }
        )
        result.append(doc_response)
    
    return result

@router.delete("/{lp_id}/documents/{lp_document_id}")
async def delete_lp_document(
        lp_id: uuid.UUID,
        lp_document_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """Delete a specific document for an LP"""
    # Check if user has appropriate role
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Find the LP document
    lp_document = db.query(LPDocument).filter(
        LPDocument.lp_id == lp_id,
        LPDocument.lp_document_id == lp_document_id
    ).first()
    
    if not lp_document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete the LP document association
    db.delete(lp_document)
    
    # Update LP status after document removal
    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if lp:
        processor = LPDocumentProcessor(db)
        new_status = processor.update_lp_status(lp)
        lp.status = new_status
        
        # Update KYC status if KYC document removed
        if lp_document.document_type == DOCUMENT_TYPES["KYC"]:
            lp.kyc_status = "Pending"
    
    db.commit()
    return {"message": "Document deleted successfully"}

# LP Status endpoints
@router.get("/{lp_id}/status", response_model=LPStatusResponse)
async def get_lp_status(
        lp_id: uuid.UUID,
        db: Session = Depends(get_db)
):
    """Get the current status of an LP"""
    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="LP not found")

    return LPStatusResponse(
        lp_id=lp.lp_id,
        status=lp.status or "Waiting for KYC",
        kyc_status=lp.kyc_status,
        status_updated=True,
        updated_at=lp.updated_at
    )

@router.patch("/{lp_id}/status", response_model=LPStatusResponse)
async def update_lp_status(
        lp_id: uuid.UUID,
        status_data: LPStatusUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """Update the status of an LP"""
    # Check if user has appropriate role
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="LP not found")

    # Update status
    lp.status = status_data.status.value
    if status_data.kyc_status:
        lp.kyc_status = status_data.kyc_status

    db.commit()
    db.refresh(lp)

    return LPStatusResponse(
        lp_id=lp.lp_id,
        status=lp.status,
        kyc_status=lp.kyc_status,
        status_updated=True,
        updated_at=lp.updated_at
    )

@router.post("/{lp_id}/documents/upload", response_model=LPDocumentResponse)
async def upload_lp_document(
        lp_id: uuid.UUID,
        file: UploadFile = File(...),
        category: str = Form(...),
        expiry_date: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Upload a document for a specific LP.
    
    Args:
        lp_id: ID of the LP
        file: The document file to upload
        category: Document category (KYC, Contribution_Agreement, CML)
        expiry_date: Optional expiry date for the document (YYYY-MM-DD format)
    
    Returns:
        LP Document response with document details
    
    The file name will be used as the document name.
    """
    # Check if user has appropriate role
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Check if LP exists
    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="LP not found")

    # Validate category
    valid_categories = ["KYC", "Contribution_Agreement", "CML"]
    if category not in valid_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )

    # Map category to document type
    category_to_doc_type = {
        "KYC": DOCUMENT_TYPES["KYC"],
        "Contribution_Agreement": DOCUMENT_TYPES["CONTRIBUTION_AGREEMENT"],
        "CML": DOCUMENT_TYPES["CML"]
    }
    document_type = category_to_doc_type[category]

    # Initialize processor
    processor = LPDocumentProcessor(db)
    uploader_email = current_user.get("sub", "unknown@example.com")

    try:
        # Process and upload the document
        await process_lp_document(
            file=file,
            lp_id=lp_id,
            doc_type=document_type,
            uploader_email=uploader_email,
            processor=processor,
            expiry_date=expiry_date
        )

        # Update LP status after document upload
        new_status = processor.update_lp_status(lp)
        lp.status = new_status
        
        # Mark KYC status as Done if KYC document uploaded
        if document_type == DOCUMENT_TYPES["KYC"]:
            lp.kyc_status = "Done"
        
        db.commit()

        # Get the uploaded document details
        lp_documents = db.query(LPDocument).filter(LPDocument.lp_id == lp_id).all()
        latest_doc = lp_documents[-1] if lp_documents else None
        
        if latest_doc:
            document = db.query(Document).filter(Document.document_id == latest_doc.document_id).first()
            return LPDocumentResponse(
                lp_document_id=latest_doc.lp_document_id,
                lp_id=latest_doc.lp_id,
                document_id=latest_doc.document_id,
                document_type=latest_doc.document_type,
                created_at=latest_doc.created_at,
                document_details={
                    "name": document.name if document else None,
                    "drive_link": document.drive_link if document else None,
                    "status": document.status if document else None,
                    "expiry_date": document.expiry_date if document else None
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve uploaded document")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

# Test endpoint to verify logging
@router.get("/test-logging")
async def test_logging():
    """Test endpoint to verify logging configuration"""
    logger.info("This is an INFO level log message")
    logger.warning("This is a WARNING level log message")
    logger.error("This is an ERROR level log message")
    print("This is a print statement for comparison")
    return {"message": "Logging test completed - check console and app.log file"}
