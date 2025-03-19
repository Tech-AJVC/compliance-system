"""
Test script for document upload with Google Drive integration.
This script demonstrates how to upload a document and link it to a task.
"""
import os
import sys
import uuid
import requests
from datetime import datetime, timedelta

# Set the API base URL
API_BASE = "http://localhost:8000"

def test_document_upload_with_task():
    """Test document upload and task linking with Google Drive integration."""
    # First, get a valid access token
    response = requests.post(
        f"{API_BASE}/api/token",
        data={
            "username": "aviral@ajuniorvc.com",  # Replace with your username
            "password": "password123"  # Replace with your password
        }
    )
    
    if not response.ok:
        print("Failed to authenticate:", response.text)
        return
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a compliance task to link the document to
    task_data = {
        "description": "Test task for document upload",
        "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
        "category": "SEBI",
        "assignee_id": "4f9c8c3c-9c3c-4f9c-8c3c-9c3c4f9c8c3c",  # Replace with a valid user ID
        "reviewer_id": "5f9c8c3c-9c3c-5f9c-8c3c-9c3c5f9c8c3c"   # Replace with a valid user ID
    }
    
    response = requests.post(
        f"{API_BASE}/api/tasks/",
        json=task_data,
        headers=headers
    )
    
    if not response.ok:
        print("Failed to create task:", response.text)
        return
    
    task_id = response.json().get("compliance_task_id")
    print(f"Created task with ID: {task_id}")
    
    # Upload a test document and link it to the task
    test_file_path = "README.md"  # Replace with a file that exists
    
    if not os.path.exists(test_file_path):
        print(f"Test file {test_file_path} does not exist.")
        return
    
    # Prepare form data for document upload
    files = {
        "file": open(test_file_path, "rb")
    }
    form_data = {
        "name": "Test Document",
        "category": "OTHER",
        "task_id": task_id
    }
    
    # Upload the document
    response = requests.post(
        f"{API_BASE}/api/documents/upload",
        files=files,
        data=form_data,
        headers=headers
    )
    
    if not response.ok:
        print("Failed to upload document:", response.text)
        return
    
    document_id = response.json().get("document_id")
    print(f"Uploaded document with ID: {document_id}")
    print(f"Document Drive links:")
    
    for link_type in ["uploader_drive_link", "assignee_drive_link", "reviewer_drive_link", "fund_manager_drive_link"]:
        link = response.json().get(link_type)
        if link:
            print(f"  - {link_type}: {link}")
    
    # Get the task details to see the document
    response = requests.get(
        f"{API_BASE}/api/tasks/{task_id}",
        headers=headers
    )
    
    if not response.ok:
        print("Failed to get task details:", response.text)
        return
    
    print("\nTask documents:")
    documents = response.json().get("documents", [])
    for doc in documents:
        print(f"  - {doc.get('name')} ({doc.get('document_id')})")
        print(f"    Link: {doc.get('drive_link')}")

if __name__ == "__main__":
    test_document_upload_with_task()
