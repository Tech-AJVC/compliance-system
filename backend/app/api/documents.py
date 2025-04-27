from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from app.utils.google_clients_gcp import drive_file_dump, get_credentials, _share_drive_file
from app.database.base import get_db
from app.models.document import Document, TaskDocument, DocumentStatus, DocumentCategory
from app.models.user import User
from app.models.compliance_task import ComplianceTask
from app.schemas.document import (
    Document as DocumentSchema,
    DocumentCreate,
    DocumentUpdate,
    TaskDocumentCreate,
    TaskDocument as TaskDocumentSchema,
    DocumentList,
    DocumentUploadResponse
)
from app.utils.file_storage import save_upload_file
from app.auth.security import get_current_user
from app.utils.audit import log_activity
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
        file: UploadFile = File(...),
        name: str = Form(...),
        category: str = Form(...),
        expiry_date: Optional[str] = Form(None),
        process_id: Optional[str] = Form(None),
        task_id: Optional[UUID] = Form(None),
        db: Session = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload a new document with metadata.
    Only users with roles Fund Manager, Compliance Officer, or Admin can upload documents.
    If task_id is provided, the document will be linked to the specified task.
    """
    # Check if user has permission to upload documents
    if current_user.get('role') not in ["Fund Manager", "Compliance Officer", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to upload documents"
        )

    # Verify task exists if task_id is provided
    task = None
    if task_id:
        task = db.query(ComplianceTask).filter(ComplianceTask.compliance_task_id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Compliance task with ID {task_id} not found"
            )

    try:
        # Save the file to local storage
        file_path = save_upload_file(file, category)

        # Create a new document record in the database
        db_document = Document(
            name=name,
            category=category,
            file_path=file_path,
            status=DocumentStatus.ACTIVE,
            process_id=process_id
        )

        if expiry_date:
            db_document.expiry_date = expiry_date

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Log document upload activity
        user_id = None
        if "sub" in current_user:
            user = db.query(User).filter(User.email == current_user["sub"]).first()
            if user:
                user_id = user.user_id

        log_activity(
            db,
            "document_upload",
            user_id,
            f"Document uploaded: {db_document.document_id} - {name} ({category})"
        )

        # Upload to Google Drive and share with appropriate users
        uploader_email = current_user.get('email')
        additional_shares = []
        fund_manager_email = "aviral@ajuniorvc.com"  # Replace with config or parameter if needed

        # If linked to a task, add task assignee and reviewer to shares
        if task:
            # Get assignee email
            assignee = db.query(User).filter(User.user_id == task.assignee_id).first()
            if assignee and assignee.email:
                additional_shares.append({"email": assignee.email, "type": "assignee", "role": "reader"})

            # Get reviewer email if exists
            if task.reviewer_id:
                reviewer = db.query(User).filter(User.user_id == task.reviewer_id).first()
                if reviewer and reviewer.email:
                    additional_shares.append({"email": reviewer.email, "type": "reviewer", "role": "reader"})
            if task.approver_id:
                approver = db.query(User).filter(User.user_id == task.approver_id).first()
                if approver and approver.email:
                    additional_shares.append({"email": approver.email, "type": "approver", "role": "reader"})
            # Add fund manager
            additional_shares.append({"email": fund_manager_email, "type": "fund_manager", "role": "reader"})

            # Create task document link
            task_document = TaskDocument(
                compliance_task_id=task_id,
                document_id=db_document.document_id
            )
            db.add(task_document)
            db.commit()
        else:
            # Always share with fund manager even if not linked to task
            additional_shares.append({"email": fund_manager_email, "type": "fund_manager", "role": "reader"})
        print(additional_shares)
        print("Uploader email:", uploader_email)
        # Upload to Drive and share
        drive_result = drive_file_dump(file_path, name, file.content_type, uploader_email, additional_shares)

        if drive_result:
            # Update document with Drive file ID and link
            db_document.drive_file_id = drive_result.get('id')

            # Store main drive link (uploader's link)
            drive_link = drive_result.get('shared_links', {}).get('uploader')
            db_document.drive_link = drive_link
            
            # Store Google Drive link as file_path instead of local path
            local_file_path = db_document.file_path
            db_document.file_path = drive_link
            
            db.commit()
            db.refresh(db_document)
            
            # Delete the local file after successful upload to Google Drive
            from app.utils.file_storage import delete_file
            delete_file(local_file_path)
            logger.info(f"Deleted local file {local_file_path} after uploading to Google Drive")

        return db_document
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/", response_model=DocumentList)
async def list_documents(
        category: Optional[str] = Query(None, description="Filter by document category"),
        status: Optional[str] = Query(None, description="Filter by document status"),
        name: Optional[str] = Query(None, description="Filter by document name"),
        skip: int = Query(0, description="Number of records to skip for pagination"),
        limit: int = Query(100, description="Maximum number of records to return"),
        db: Session = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all documents with optional filters.
    Includes pagination support with skip and limit parameters.
    """
    query = db.query(Document)

    # Apply filters if provided
    if category:
        query = query.filter(Document.category == category)
    if status:
        query = query.filter(Document.status == status)
    if name:
        query = query.filter(Document.name.ilike(f"%{name}%"))

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    documents = query.offset(skip).limit(limit).all()

    return {"documents": documents, "total": total}


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
        document_id: UUID,
        db: Session = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific document by ID.
    """
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    return document


# @router.post("/{document_id}/link-to-task", response_model=TaskDocumentSchema)
# async def link_document_to_task(
#     document_id: UUID,
#     task_link: TaskDocumentCreate,
#     db: Session = Depends(get_db),
#     current_user: Dict[str, Any] = Depends(get_current_user)
# ):
#     """
#     Link a document to a compliance task.
#     Also shares the document with task assignee, reviewer, and fund manager.
#     """
#     # Verify document exists
#     document = db.query(Document).filter(Document.document_id == document_id).first()
#     if not document:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Document with ID {document_id} not found"
#         )

#     # Verify task exists
#     task = db.query(ComplianceTask).filter(ComplianceTask.compliance_task_id == task_link.compliance_task_id).first()
#     if not task:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Compliance task with ID {task_link.compliance_task_id} not found"
#         )

#     # Check if link already exists
#     existing_link = db.query(TaskDocument).filter(
#         and_(
#             TaskDocument.document_id == document_id,
#             TaskDocument.compliance_task_id == task_link.compliance_task_id
#         )
#     ).first()

#     if existing_link:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="This document is already linked to the specified task"
#         )

#     # Create the link
#     task_document = TaskDocument(
#         compliance_task_id=task_link.compliance_task_id,
#         document_id=document_id
#     )

#     db.add(task_document)
#     db.commit()
#     db.refresh(task_document)

#     # Share document in Google Drive if it has a drive_file_id
#     if document.drive_file_id:
#         additional_shares = []
#         fund_manager_email = "aviral@ajuniorvc.com"

#         # Get assignee email
#         assignee = db.query(User).filter(User.user_id == task.assignee_id).first()
#         if assignee and assignee.email:
#             additional_shares.append({"email": assignee.email, "type": "assignee", "role": "reader"})

#         # Get reviewer email if exists
#         if task.reviewer_id:
#             reviewer = db.query(User).filter(User.user_id == task.reviewer_id).first()
#             if reviewer and reviewer.email:
#                 additional_shares.append({"email": reviewer.email, "type": "reviewer", "role": "reader"})

#         # Add fund manager
#         additional_shares.append({"email": fund_manager_email, "type": "fund_manager", "role": "reader"})

#         # Share with additional users
#         creds = get_credentials()
#         service = build("drive", "v3", credentials=creds)

#         for email_info in additional_shares:
#             try:
#                 email = email_info.get('email')
#                 role = email_info.get('role', 'reader')
#                 link = _share_drive_file(service, document.drive_file_id, email, role)

#                 # Update document with links
#                 if email_info.get('type') == 'assignee':
#                     document.assignee_drive_link = link
#                 elif email_info.get('type') == 'reviewer':
#                     document.reviewer_drive_link = link
#                 elif email_info.get('type') == 'fund_manager':
#                     document.fund_manager_drive_link = link
#             except Exception as e:
#                 logger.error(f"Error sharing document with {email_info.get('email')}: {str(e)}")

#         db.commit()

#     # Log document link activity
#     user_id = None
#     if "sub" in current_user:
#         user = db.query(User).filter(User.email == current_user["sub"]).first()
#         if user:
#             user_id = user.user_id

#     log_activity(
#         db,
#         "document_task_link",
#         user_id,
#         f"Document {document_id} linked to task {task_link.compliance_task_id}"
#     )

#     return task_document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
        document_id: UUID,
        db: Session = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a document (only for Admin users).
    """
    # Only Admin users can delete documents
    if current_user.get('role') not in ["Admin", "Fund Manager", "Compliance Officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin users can delete documents"
        )

    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    # Delete all task document links first
    db.query(TaskDocument).filter(TaskDocument.document_id == document_id).delete()

    # Delete the document
    db.delete(document)
    db.commit()

    logger.info(f"Document {document_id} deleted by user {current_user.get('sub')}")
    return None
