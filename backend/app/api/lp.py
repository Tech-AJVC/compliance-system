from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
from app.database.base import get_db
from app.models.lp_details import LPDetails
from app.models.lp_drawdowns import LPDrawdown
from app.schemas.lp import (
    LPDetailsCreate, LPDetailsUpdate, LPDetailsResponse,
    LPDrawdownCreate, LPDrawdownUpdate, LPDrawdownResponse,
    LPWithDrawdowns
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

router = APIRouter()


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
                        hashed_password = get_password_hash(random_password)

                        # Create user with LP role and same ID
                        db_user = User(
                            user_id=new_lp.lp_id,
                            name=new_lp.lp_name,
                            email=new_lp.email,
                            role="LP",
                            password_hash=hashed_password,
                            mfa_enabled=False,
                            phone=new_lp.mobile_no
                        )
                        gmail_send_email("tech@ajuniorvc.com", db_user.email, "User Created Notification",
                                         f"A new user has been created:\n\n"
                                         f"Name: {new_lp.lp_name}\n"
                                         f"Email: {new_lp.email}\n"
                                         f"Role: LP\n"
                                         f"Password: {hashed_password}")

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
        lp_data: LPDetailsCreate,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Create a new LP (Limited Partner) record.
    """
    # Check if user has appropriate role
    if current_user.get("role") not in ["Fund Manager", "Compliance Officer", "Fund Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have one of the required roles: Fund Manager, Compliance Officer, Fund Admin"
        )

    # Generate a UUID to use for both LP and User
    lp_user_id = uuid.uuid4()

    # Create new LP record with the generated UUID
    new_lp = LPDetails(lp_id=lp_user_id, **lp_data.model_dump())

    try:
        # Add and commit the LP record
        db.add(new_lp)
        db.commit()
        db.refresh(new_lp)

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
                hashed_password = get_password_hash(random_password)

                # Create user with LP role and same ID
                db_user = User(
                    user_id=new_lp.lp_id,
                    name=new_lp.lp_name,
                    email=new_lp.email,
                    role="LP",
                    password_hash=hashed_password,
                    mfa_enabled=False,
                    phone=new_lp.mobile_no
                )
                gmail_send_email("tech@ajuniorvc.com", db_user.email, "User Created Notification",
                                 f"A new user has been created:\n\n"
                                 f"Name: {new_lp.lp_name}\n"
                                 f"Email: {new_lp.email}\n"
                                 f"Role: LP\n"
                                 f"Password: {hashed_password}")

                # Add and commit the user record
                db.add(db_user)
                db.commit()
                db.refresh(db_user)

            print(f"Created user account for LP: {new_lp.lp_name} with ID: {new_lp.lp_id}")
            print(f"Generated temporary password: {random_password}")

            # TODO: Send email with temporary password to the LP
            # Uncomment the following code once email sending is properly configured
            # try:
            #     gmail_send_email(
            #         subject_email="your-email@example.com",
            #         recipient_email=new_lp.email,
            #         subject="Your Account Details",
            #         body=f"Your account has been created. Your temporary password is: {random_password}"
            #     )
            # except Exception as email_err:
            #     print(f"Error sending welcome email: {str(email_err)}")

        except Exception as user_err:
            # Log the error but don't fail the LP creation if user creation fails
            print(f"Error creating user account for LP: {str(user_err)}")

        # Log the activity
        try:
            # Print the current_user dictionary to see what keys are available
            print(f"Current user: {current_user}")
            user_email = current_user.get("sub")
            user = db.query(User).filter(User.email == user_email).first()
            log_activity(
                db=db,
                activity="lp_created",
                user_id=user.user_id,
                details=f"Created LP: {new_lp.lp_name}"
            )
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
            # Continue even if logging fails

        return new_lp
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LP with this email or PAN already exists"
        )


@router.get("/", response_model=List[LPDetailsResponse])
async def get_all_lps(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Get all LP records with pagination.
    """
    lps = db.query(LPDetails).offset(skip).limit(limit).all()
    return lps


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
            print(f"Current user: {get_current_user()}")

            log_activity(
                db=db,
                activity="lp_updated",
                user_id=uuid.UUID(get_current_user().get("sub", "00000000-0000-0000-0000-000000000000")),
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
    Delete an LP record.
    """
    # Check if user has appropriate role
    check_role(["Fund Manager", "Fund Admin"])

    lp = db.query(LPDetails).filter(LPDetails.lp_id == lp_id).first()
    if not lp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LP not found"
        )

    # Log before deletion
    lp_name = lp.lp_name

    db.delete(lp)
    db.commit()

    # Log the activity
    try:
        # Print the current_user dictionary to see what keys are available
        print(f"Current user: {get_current_user()}")

        log_activity(
            db=db,
            activity="lp_deleted",
            user_id=uuid.UUID(get_current_user().get("sub", "00000000-0000-0000-0000-000000000000")),
            details=f"Deleted LP: {lp_name}"
        )
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        # Continue even if logging fails

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
            user_id=uuid.UUID(get_current_user().get("sub", "00000000-0000-0000-0000-000000000000")),
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
        print(f"Current user: {get_current_user()}")

        log_activity(
            db=db,
            activity="drawdown_updated",
            user_id=uuid.UUID(get_current_user().get("sub", "00000000-0000-0000-0000-000000000000")),
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
        print(f"Current user: {get_current_user()}")

        log_activity(
            db=db,
            activity="drawdown_deleted",
            user_id=uuid.UUID(get_current_user().get("sub", "00000000-0000-0000-0000-000000000000")),
            details=f"Deleted drawdown: {drawdown_id}"
        )
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        # Continue even if logging fails

    return None
