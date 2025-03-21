import sys
import os
import json
import base64
from fastapi import HTTPException
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading
import socket
import datetime


"""
This module demonstrates how to implement reusable authentication
for several Google APIs including Gmail, Google Drive, and Google Calendar
using a service account (or a pre‐authenticated credential).
No interactive authorization is needed at runtime.
"""

import os
import base64
from email.message import EmailMessage

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.oauth2 import service_account

SCOPES = [
"https://www.googleapis.com/auth/gmail.compose",  # For creating Gmail drafts or sending emails.
"https://www.googleapis.com/auth/drive.file",     # For uploading files to Drive.
"https://www.googleapis.com/auth/calendar" , 
"https://www.googleapis.com/auth/gmail.send"      # For creating Google Calendar events.
]


GOOGLE_APPLICATION_CREDENTIALS = '/Users/abhinavbhatnagar/Documents/Compliance/compliance-system/backend/app/utils/neat-height-449308-h8-2a37363e5a04.json'

def get_credentials(subject_email: str = None):
    """
    Returns credentials from a service account file with the configured scopes.
    If a subject_email is provided (required for delegated access, e.g. Gmail),
    credentials will be impersonated to that user.

    The code expects the environment variable GOOGLE_APPLICATION_CREDENTIALS
    to point to the service account JSON key file.

    Args:
    subject_email: (Optional) User email to impersonate for domain-wide delegation.
    Returns:
    google.oauth2.service_account.Credentials object.
    """
    service_account_file = GOOGLE_APPLICATION_CREDENTIALS
    if not service_account_file:
        raise EnvironmentError("Environment variable GOOGLE_APPLICATION_CREDENTIALS is not set")

    creds = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES)

    # If you need to access user data with Gmail, you must delegate domain-wide access.
    if subject_email:
        creds = creds.with_subject(subject_email)

    return creds

def gmail_create_draft(subject_email: str):
    """
    Creates a Gmail draft using the pre-authorized credentials.

    Args:
    subject_email: The email address of the user to impersonate (must be allowed by domain-wide delegation).

    Returns:
    The created Gmail draft object (or None if an error occurred).
    """
    # Get credentials delegated to the target Gmail user.
    creds = get_credentials(subject_email)
    print("Creds")
    print(creds)

    try:
        service = build("gmail", "v1", credentials=creds)
        
        # Construct the email message.
        message = EmailMessage()
        message.set_content("This is an automated draft email created in production-grade code.")
        message["To"] = "aviral@ajuniorvc.com"
        message["From"] = subject_email  # Use the impersonated email as the sender.
        message["Subject"] = "Automated draft"
        
        # Encode the message and prepare the draft request.
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"message": {"raw": encoded_message}}
        
        draft = service.users().drafts().create(userId="me", body=create_message).execute()
        print(f"[Gmail] Draft id: {draft['id']}\nDraft message: {draft['message']}")
        return draft

    except HttpError as error:
        print(f"[Gmail] An error occurred: {error}")
        return None

def gmail_send_email(subject_email: str, recipient_email: str, subject: str, body: str):
    # creds = service_account.Credentials.from_service_account_file(
    #     "PATH_TO_SERVICE_ACCOUNT_KEY.json", scopes=SCOPES
    # ).with_subject("USER_TO_IMPERSONATE@DOMAIN.com")
    creds = get_credentials(subject_email)
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()
    message.set_content(body)
    message["To"] = recipient_email
    message["From"] = subject_email
    message["Subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": encoded_message}
    sent = service.users().messages().send(userId="me", body=body).execute()
    print(f"[Gmail] Email sent: {message}")


def drive_file_dump(file_path: str, file_name: str, mime_type: str, share_with_email: str = None, additional_shares: list = None):
    """
    Uploads a file to Google Drive using the pre-authorized credentials.

    Args:
    file_path: Local path to the file.
    file_name: Name to assign to the file on Drive.
    mime_type: MIME type of the file.
    share_with_email: Email address to share the file with after upload (uploader).
    additional_shares: List of additional emails to share the file with (optional).
    
    Returns:
    Dictionary containing the uploaded file's metadata and shared links.
    """
    # For Drive we do not need to impersonate unless required; here we use the service account's identity.
    creds = get_credentials()

    try:
        service = build("drive", "v3", credentials=creds)
        
        # Prepare file metadata and media.
        file_metadata = {"name": file_name}
        # The MediaFileUpload class is in googleapiclient.http.
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(file_path, mimetype=mime_type)
        
        file = service.files().create(
            body=file_metadata, media_body=media, fields="id,name,webViewLink"
        ).execute()
        
        file_id = file.get('id')
        print(f"[Drive] Uploaded file with ID: {file_id} and name: {file.get('name')}")
        
        # Initialize result dictionary
        result = {
            'id': file_id,
            'name': file.get('name'),
            'shared_links': {}
        }
        
        # Share with uploader if provided
        if share_with_email:
            link = _share_drive_file(service, file_id, share_with_email)
            result['shared_links']['uploader'] = link
        
        # Share with additional emails if provided
        if additional_shares:
            for email_info in additional_shares:
                email = email_info.get('email')
                role = email_info.get('role', 'reader')
                if email:
                    link = _share_drive_file(service, file_id, email, role)
                    #  Overwrite since the link is the same
                    result['shared_links']['uploader'] = link
        return result

    except HttpError as error:
        print(f"[Drive] An error occurred: {error}")
        return None

def _share_drive_file(service, file_id, email, role='reader'):
    """
    Helper function to share a Drive file with a specific email.
    
    Args:
    service: Drive API service instance.
    file_id: ID of the file to share.
    email: Email address to share with.
    role: Permission role, default is 'reader'.
    
    Returns:
    The web view link of the shared file.
    """
    try:
        # Create the permission
        user_permission = {
            'type': 'user',
            'role': role,  # Can be 'reader', 'writer', or 'owner'
            'emailAddress': email
        }
        
        # Share the file
        service.permissions().create(
            fileId=file_id,
            body=user_permission,
            sendNotificationEmail=True
        ).execute()
        
        # Get the file to retrieve the webViewLink
        file = service.files().get(fileId=file_id, fields="webViewLink").execute()
        web_view_link = file.get('webViewLink')
        
        print(f"[Drive] Shared file with: {email} (role: {role})")
        print(f"[Drive] File can be viewed at: {web_view_link}")
        
        return web_view_link
    except HttpError as error:
        print(f"[Drive] An error sharing with {email}: {error}")
        return None

def calendar_create_event(subject_email: str, event: dict):
    """
    Creates a Google Calendar event using the pre-authorized credentials.

    Args:
    subject_email: The email address of the user to impersonate.
    event: A dictionary defining the event details as per the Calendar API spec.
    
    Returns:
    The created event object (or None if an error occurred).
    """
    # Calendar events that affect a user's calendar typically require the user's delegated credentials.
    creds = get_credentials(subject_email)

    try:
        service = build("calendar", "v3", credentials=creds)
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        print(f"[Calendar] Event created: {created_event.get('htmlLink')}")
        return created_event

    except HttpError as error:
        print(f"[Calendar] An error occurred: {error}")
        return None


if __name__ == "__main__":
    # gmail_create_draft("tech@ajuniorvc.com")
    # subject_email: str, recipient_email: str, subject: str, body: str)
    # gmail_send_email("tech@ajuniorvc.com", "aviral@ajuniorvc.com", "Test", "Compliance System Test Email")
    drive_file_dump("/Users/abhinavbhatnagar/Documents/Compliance/compliance-system/backend/uploads/Other/7a08a129-b121-4dea-87fb-574daf7d8e41.pdf", "LOR.pdf", "application/pdf", "abhinav7bhatnagar@gmail.com", [{"email": "tech@ajuniorvc.com", "type": "fund_manager", "role": "reader"}])