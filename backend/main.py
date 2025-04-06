from fastapi import FastAPI, Depends, HTTPException, status, Form, Query, Security
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.models.user import User
from app.models.compliance_task import ComplianceTask, TaskState, TaskCategory
from app.models.document import Document, TaskDocument
from app.auth.security import get_password_hash, verify_password, create_access_token, get_current_user, check_role
from app.schemas.compliance_task import (
    ComplianceTaskCreate,
    ComplianceTaskResponse,
    ComplianceTaskUpdate,
    TaskState,
    TaskCategory,
    ComplianceTaskList
)
from app.api.documents import router as documents_router
from app.api.reports import router as reports_router
from app.api.lp import router as lp_router
from app.api.compliance import router as compliance_router
from app.api.audit import router as audit_router
from app.utils.audit import log_activity
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import uuid
from datetime import timedelta, datetime
from sqlalchemy.exc import IntegrityError
import traceback
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer, HTTPBasic, HTTPBasicCredentials
import os
import secrets
from app.utils.google_clients_gcp import gmail_send_email
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import config
from sqlalchemy import func
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# Get authentication credentials from config
DOCS_USERNAME = "abhi7"
DOCS_PASSWORD = "comp$135!" 

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Add HTTPS redirect middleware to ensure all requests use HTTPS
# app.add_middleware(HTTPSRedirectMiddleware)

# Configure CORS using settings from config.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
    expose_headers=config.CORS_EXPOSE_HEADERS,
    max_age=config.CORS_MAX_AGE,
)


# HTTP Basic security scheme
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Security(security)):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Custom OpenAPI route that requires authentication
@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(username: str = Depends(get_current_username)):
    return get_openapi(
        title="Compliance System API",
        version="1.0.0",
        description="API for the Compliance System",
        routes=app.routes,
    )

# Custom Swagger UI route that requires authentication
@app.get("/docs", include_in_schema=False)
async def get_documentation(username: str = Depends(get_current_username)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Compliance System API")

# Custom Redoc route that requires authentication
@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(username: str = Depends(get_current_username)):
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(openapi_url="/openapi.json", title="Compliance System API")

# Mount the routers
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(lp_router, prefix="/api/lps", tags=["lps"])
app.include_router(compliance_router, prefix="/api/compliance", tags=["compliance"])
app.include_router(audit_router, prefix="/api/audit", tags=["audit"])

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: str
    password: str
    mfa_enabled: bool = False
    phone: Optional[str] = None


class UserResponse(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    role: str
    mfa_enabled: bool
    phone: Optional[str]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class UserSearchResponse(BaseModel):
    UserId: uuid.UUID
    UserName: str
    email: str
    role: str

    class Config:
        from_attributes = True
        alias_generator = lambda field_name: field_name  # Keep field names as defined


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user with this email already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash the password before storing
        hashed_password = get_password_hash(user.password)

        # Validate role
        # Fund Manager, Compliance Officer, LP, Portfolio Company, Auditor, Legal Consultant, Fund Admin
        valid_roles = ["Fund Manager", "Compliance Officer", "LP", "Portfolio Company", "Auditor", "Legal Consultant"]

        if user.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )

        db_user = User(
            name=user.name,
            email=user.email,
            role=user.role,
            password_hash=hashed_password,
            mfa_enabled=user.mfa_enabled,
            phone=user.phone
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unexpected error: {str(e)}\nDetails: {error_details}"
        )


@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log successful login
    log_activity(db, "login", user.user_id, f"User {user.email} logged in")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users/search", response_model=List[UserSearchResponse])
async def search_users(
        username: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Search for users based on username using ILIKE match.
    Returns all users that match the provided username pattern.
    """
    # Check if current user has required permissions
    # Simple implementation: all authenticated users can search

    # Perform the search with ILIKE to make it case-insensitive
    matching_users = db.query(User).filter(
        User.name.ilike(f"%{username}%")
    ).all()

    # Log the search activity
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if user:
        log_activity(
            db,
            "user_search",
            user.user_id,
            f"User search performed with query: {username}"
        )

    # Map database fields to response schema fields
    results = []
    for user in matching_users:
        results.append({
            "UserId": user.user_id,
            "UserName": user.name,
            "email": user.email,
            "role": user.role
        })

    return results


@app.get("/api/fund-manager/dashboard")
async def fund_manager_dashboard(current_user: dict = Depends(check_role("Fund Manager"))):
    return {
        "message": "Welcome to Fund Manager Dashboard",
        "user": current_user["sub"]
    }


# Compliance Tasks Endpoints

@app.post("/api/tasks/", response_model=ComplianceTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
        task: ComplianceTaskCreate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        # Validate assignee exists
        assignee = db.query(User).filter(User.user_id == task.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee not found")

        # Validate dependent task if specified
        if task.dependent_task_id:
            dependent_task = db.query(ComplianceTask).filter(
                ComplianceTask.compliance_task_id == task.dependent_task_id
            ).first()
            if not dependent_task:
                raise HTTPException(status_code=404, detail="Dependent task not found")

        db_task = ComplianceTask(**task.model_dump())
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        # Log task creation
        user_id = None
        if "sub" in current_user:
            user = db.query(User).filter(User.email == current_user["sub"]).first()
            if user:
                user_id = user.user_id

        log_activity(
            db,
            "task_created",
            user_id,
            f"Task created: {db_task.compliance_task_id} - {task.description}"
        )

        # credentials_file = os.path.join("./backend/app/utils", "credentials.json")

        # credentials = authenticate_user(user_id, credentials_file)
        # if not credentials:
        #     return {"error": "Authentication failed"}

        # Prepare the email notification with additional details
        gmail_send_email("tech@ajuniorvc.com", "aviral@ajuniorvc.com", "Task Created Notification",
                         f"A new task has been created:\n\n"
                         f"Task ID: {db_task.compliance_task_id}\n"
                         f"Task Details: {task.description}\n"
                         f"Category: {db_task.category}\n"
                         f"Due Date: {db_task.deadline.strftime('%Y-%m-%d') if db_task.deadline else 'Not specified'}\n"
                         f"Assignee: {assignee.name if assignee else 'Not assigned'}")
        return db_task

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        # if not credentials:
        #     return {"error": "Authentication failed"}
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/tasks/", response_model=ComplianceTaskList)
async def get_tasks(
        state: Optional[str] = None,
        category: Optional[str] = None,
        assignee_id: Optional[uuid.UUID] = None,
        assignee_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort: Optional[str] = None,
        skip: int = Query(0, description="Number of records to skip for pagination"),
        limit: int = Query(100, description="Maximum number of records to return"),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get tasks with optional filtering and sorting:
    - Filter by task state
    - Filter by task category
    - Filter by assignee_id
    - Filter by assignee_name (partial match)
    - Filter by deadline date range (start_date to end_date)
    - Sort by deadline (ascending or descending)
    - Pagination support (skip and limit)
    """
    # Start with a query that joins ComplianceTask with User (for assignee filtering by name)
    # Select both ComplianceTask and User.name for the assignee
    query = db.query(ComplianceTask, User.name.label('assignee_name')).join(
        User,
        ComplianceTask.assignee_id == User.user_id,
        isouter=True
    )

    # Apply filters
    if state:
        query = query.filter(ComplianceTask.state == state)

    if category:
        query = query.filter(ComplianceTask.category == category)

    if assignee_id:
        query = query.filter(ComplianceTask.assignee_id == assignee_id)

    if assignee_name:
        query = query.filter(User.name.ilike(f"%{assignee_name}%"))

    # Filter by date range if provided
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(func.date(ComplianceTask.deadline) >= start)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(func.date(ComplianceTask.deadline) <= end)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )

    # Sorting
    if sort:
        if sort == "deadline_asc":
            query = query.order_by(ComplianceTask.deadline.asc())
        elif sort == "deadline_desc":
            query = query.order_by(ComplianceTask.deadline.desc())
        elif sort == "status_asc":
            query = query.order_by(ComplianceTask.state.asc())
        elif sort == "status_desc":
            query = query.order_by(ComplianceTask.state.desc())
        elif sort == "assignee_asc":
            query = query.order_by(User.name.asc())
        elif sort == "assignee_desc":
            query = query.order_by(User.name.desc())
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid sort parameter. Use 'deadline_asc', 'deadline_desc', 'status_asc', 'status_desc', 'assignee_asc', or 'assignee_desc'."
            )

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    results = query.offset(skip).limit(limit).all()

    # Process results to include assignee_name in each task
    tasks = []
    for task, assignee_name in results:
        # Convert SQLAlchemy model to dict and add assignee_name
        task_dict = task.__dict__.copy()
        task_dict['assignee_name'] = assignee_name

        # Get reviewer name
        reviewer_name = None
        if task.reviewer_id:
            reviewer = db.query(User).filter(User.user_id == task.reviewer_id).first()
            if reviewer:
                reviewer_name = reviewer.name
        task_dict['reviewer_name'] = reviewer_name

        # Get approver name
        approver_name = None
        if task.approver_id:
            approver = db.query(User).filter(User.user_id == task.approver_id).first()
            if approver:
                approver_name = approver.name
        task_dict['approver_name'] = approver_name

        # Get associated documents with appropriate drive links
        task_documents = db.query(TaskDocument).filter(
            TaskDocument.compliance_task_id == task.compliance_task_id
        ).all()

        # Get document details
        documents = []
        for task_doc in task_documents:
            document = db.query(Document).filter(
                Document.document_id == task_doc.document_id
            ).first()

            if document:
                document_info = {
                    "document_id": document.document_id,
                    "name": document.name,
                    "category": document.category,
                    "drive_link": document.drive_link  # Use the new common drive_link field
                }

                # Legacy code for backward compatibility - can be removed once everything is migrated
                if not document_info["drive_link"]:
                    # Determine which link to provide based on user role
                    user_email = current_user.get('email')
                    is_fund_manager = user_email == "aviral@ajuniorvc.com"
                documents.append(document_info)

        task_dict['documents'] = documents
        tasks.append(task_dict)

    return {"tasks": tasks, "total": total}


@app.get("/api/tasks/{task_id}", response_model=ComplianceTaskResponse)
async def get_task(
        task_id: uuid.UUID,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get details of a specific task by ID, including linked documents.
    """
    task = db.query(ComplianceTask).filter(ComplianceTask.compliance_task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get assignee name
    assignee_name = None
    if task.assignee_id:
        assignee = db.query(User).filter(User.user_id == task.assignee_id).first()
        if assignee:
            assignee_name = assignee.name

    # Get reviewer name
    reviewer_name = None
    if task.reviewer_id:
        reviewer = db.query(User).filter(User.user_id == task.reviewer_id).first()
        if reviewer:
            reviewer_name = reviewer.name

    # Get approver name
    approver_name = None
    if task.approver_id:
        approver = db.query(User).filter(User.user_id == task.approver_id).first()
        if approver:
            approver_name = approver.name

    # Create task dictionary with assignee_name
    task_dict = task.__dict__.copy()
    task_dict['assignee_name'] = assignee_name
    task_dict['reviewer_name'] = reviewer_name
    task_dict['approver_name'] = approver_name

    # Get associated documents with appropriate drive links
    task_documents = db.query(TaskDocument).filter(
        TaskDocument.compliance_task_id == task.compliance_task_id
    ).all()

    # Get document details
    documents = []
    for task_doc in task_documents:
        document = db.query(Document).filter(
            Document.document_id == task_doc.document_id
        ).first()

        if document:
            document_info = {
                "document_id": document.document_id,
                "name": document.name,
                "category": document.category,
                "drive_link": document.drive_link  # Use the new common drive_link field
            }

            # Legacy code for backward compatibility - can be removed once everything is migrated
            if not document_info["drive_link"]:
                # Determine which link to provide based on user role
                user_email = current_user.get('email')
                is_fund_manager = user_email == "aviral@ajuniorvc.com"

            documents.append(document_info)

    task_dict['documents'] = documents

    return task_dict


@app.patch("/api/tasks/{task_id}", response_model=ComplianceTaskResponse)
async def update_task(
        task_id: uuid.UUID,
        task_update: ComplianceTaskUpdate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_task = db.query(ComplianceTask).filter(ComplianceTask.compliance_task_id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if trying to complete a task with incomplete dependency
    if (task_update.state == TaskState.COMPLETED and db_task.dependent_task_id):
        dependent_task = db.query(ComplianceTask).filter(
            ComplianceTask.compliance_task_id == db_task.dependent_task_id
        ).first()
        if dependent_task and dependent_task.state != TaskState.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Cannot complete task: dependent task is not completed"
            )
    # Update task fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    try:
        db.commit()
        db.refresh(db_task)
        # Get assignee name for the email
        assignee_name = "Not assigned"
        if db_task.assignee_id:
            assignee = db.query(User).filter(User.user_id == db_task.assignee_id).first()
            if assignee:
                assignee_name = assignee.name
                
        # Prepare the email notification with additional details
        gmail_send_email("tech@ajuniorvc.com", "aviral@ajuniorvc.com", "Task Updated Notification",
                         f"A task has been updated:\n\n"
                         f"Task ID: {db_task.compliance_task_id}\n"
                         f"Task Details: {db_task.description}\n"
                         f"Category: {db_task.category}\n"
                         f"Due Date: {db_task.deadline.strftime('%Y-%m-%d') if db_task.deadline else 'Not specified'}\n"
                         f"Assignee: {assignee_name}")
        return db_task
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
