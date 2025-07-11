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
import re
import io


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
from googleapiclient.http import MediaIoBaseDownload

from google.oauth2 import service_account
import pandas as pd

SCOPES = [
"https://www.googleapis.com/auth/gmail.compose",  # For creating Gmail drafts or sending emails.
"https://www.googleapis.com/auth/drive.file",     # For uploading files to Drive.
"https://www.googleapis.com/auth/calendar" , 
"https://mail.google.com/",
"https://www.googleapis.com/auth/gmail.send",     # For creating Google Calendar events.
"https://www.googleapis.com/auth/drive",           # For full access to Drive files
"https://www.googleapis.com/auth/spreadsheets",         # For full access to Google Sheets
"https://www.googleapis.com/auth/spreadsheets.readonly"  # For reading Google Sheets
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

    print(f"Service account file path: {service_account_file}")
    print(f"Scopes being used: {SCOPES}")
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
    print(creds)
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


def test_gmail_connection(user_email):
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES, subject=user_email)

    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        print("Gmail API is working correctly (labels retrieved).")
        return True
    except Exception as e:
        print(f"Gmail API test failed: {e}")
        return False


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


def download_drive_file(drive_link: str, local_folder_path: str):
    """
    Downloads a file from a Google Drive link to a local folder.
    
    Args:
    drive_link: The Google Drive link to the file (https://drive.google.com/file/d/FILE_ID/...).  
    local_folder_path: The local folder path where the file should be saved.
    
    Returns:
    Dictionary containing the downloaded file's local path and filename.
    """
    # For Drive we do not need to impersonate unless required
    creds = get_credentials()
    
    try:
        # Extract file ID from the Drive link
        file_id_match = re.search(r'(/d/|id=)([a-zA-Z0-9_-]+)', drive_link)
        if not file_id_match:
            raise ValueError(f"Could not extract file ID from Drive link: {drive_link}")
            
        file_id = file_id_match.group(2)
        
        # Build the Drive service
        service = build("drive", "v3", credentials=creds)
        
        # Get file metadata to determine the filename
        file_metadata = service.files().get(fileId=file_id, fields="name,mimeType").execute()
        filename = file_metadata.get('name')
        mime_type = file_metadata.get('mimeType')
        
        # Make sure the local folder exists
        os.makedirs(local_folder_path, exist_ok=True)
        
        # Build the local file path
        local_file_path = os.path.join(local_folder_path, filename)
        
        # Download the file
        request = service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"[Drive] Download progress: {int(status.progress() * 100)}%")
        
        # Save the file to disk
        file_handle.seek(0)
        with open(local_file_path, 'wb') as f:
            f.write(file_handle.read())
        
        print(f"[Drive] File downloaded to: {local_file_path}")
        
        # Return details about the downloaded file
        return {
            'local_path': local_file_path,
            'filename': filename,
            'mime_type': mime_type
        }
        
    except HttpError as error:
        print(f"[Drive] An error occurred: {error}")
        return None
    except Exception as e:
        print(f"[Drive] An unexpected error occurred: {e}")
        return None

def read_google_sheets(sheets_link: str, sheet_name: str = None, range_name: str = None):
    """
    Reads data from a Google Sheets document.
    
    Args:
    sheets_link: The Google Sheets URL (https://docs.google.com/spreadsheets/d/SHEET_ID/...).  
    sheet_name: Optional name of the specific sheet to read. If None, reads the first sheet.
    range_name: Optional cell range to read (e.g., 'A1:D10'). If None, reads all data.
    
    Returns:
    DataFrame containing the sheet data.
    """
    # For Sheets we may need to impersonate for proper authorization - using default credential
    # You might need to modify this if the sheets require specific user access
    creds = get_credentials()
    
    try:
        # Method 1: Direct extraction from URL path
        if 'spreadsheets/d/' in sheets_link:
            parts = sheets_link.split('spreadsheets/d/')[1]
            spreadsheet_id = parts.split('/')[0].split('?')[0].split('#')[0]
        elif '/d/' in sheets_link:
            parts = sheets_link.split('/d/')[1]
            spreadsheet_id = parts.split('/')[0].split('?')[0].split('#')[0]
        else:
            raise ValueError(f"Could not extract spreadsheet ID from link: {sheets_link}")
        
        print(f"Extracted spreadsheet ID: {spreadsheet_id}")
        
        # Build the Sheets service
        service = build("sheets", "v4", credentials=creds)
        
        # If sheet_name is provided, we need to find its gid
        if sheet_name:
            # Get all sheet metadata first
            spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = spreadsheet_metadata.get('sheets', [])
            
            # Find the sheet by name
            sheet_found = False
            for sheet in sheets:
                properties = sheet.get('properties', {})
                if properties.get('title') == sheet_name:
                    sheet_found = True
                    range_to_read = f"'{sheet_name}'" + (f"!{range_name}" if range_name else "")
                    break
                    
            if not sheet_found:
                print(f"[Sheets] Sheet '{sheet_name}' not found. Using first sheet instead.")
                range_to_read = range_name if range_name else ""
        else:
            range_to_read = range_name if range_name else ""
        
        print("Building sheets service...")
        service = build("sheets", "v4", credentials=creds)
        print("Service built successfully")

        # Important: Make sure the Google Sheet is shared with the service account email
        # You can find this email in your service account JSON file or in the Google Cloud Console
        print("Attempting to access spreadsheet...")

        # For debugging
        try:
            info = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            print(f"Successfully connected to sheet: {info.get('properties', {}).get('title')}")
        except HttpError as e:
            print(f"Error accessing spreadsheet: {e}")
            if '404' in str(e):
                print("IMPORTANT: Make sure the spreadsheet exists and is shared with your service account email.")
                print(f"Your service account might be: {creds.service_account_email if hasattr(creds, 'service_account_email') else 'Unknown'}")
            raise

        # Check if we need to target a specific sheet
        if sheet_name:
            sheets = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute().get('sheets', [])
            sheet_found = False
            for sheet in sheets:
                if sheet.get('properties', {}).get('title') == sheet_name:
                    sheet_found = True
                    range_to_read = f"'{sheet_name}'" + (f"!{range_name}" if range_name else "")
                    break
                    
            if not sheet_found:
                print(f"Sheet '{sheet_name}' not found. Available sheets: {[s.get('properties', {}).get('title') for s in sheets]}")
                range_to_read = range_name if range_name else "Sheet1"
        else:
            # If no sheet name specified, use the first sheet or the range name if provided
            range_to_read = range_name if range_name else "Sheet1"

        print(f"Reading range: {range_to_read if range_to_read else 'default sheet'}")
        
        # Read the data from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_to_read,
            valueRenderOption="UNFORMATTED_VALUE"
        ).execute()
        
        # Extract the values
        values = result.get('values', [])
        
        if not values:
            print("[Sheets] No data found in the specified sheet.")
            return pd.DataFrame()
            
        # Convert to DataFrame - assuming first row is headers
        headers = values[0]
        data = values[1:] if len(values) > 1 else []
        
        # Pad rows with None values if they're shorter than the header row
        for row in data:
            while len(row) < len(headers):
                row.append(None)
                
        # Create the DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        print(f"[Sheets] Successfully read {len(df)} rows from the Google Sheet")
        return df
        
    except HttpError as error:
        print(f"[Sheets] An error occurred: {error}")
        return pd.DataFrame()
    except Exception as e:
        print(f"[Sheets] An unexpected error occurred: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
        gmail_create_draft("tech@ajuniorvc.com")
        # subject_email: str, recipient_email: str, subject: str, body: str)
        # gmail_send_email("tech@ajuniorvc.com", "aviral@ajuniorvc.com", "Test", "Compliance System Test Email")
        # drive_file_dump("/Users/abhinavbhatnagar/Documents/Compliance/compliance-system/backend/uploads/Other/7a08a129-b121-4dea-87fb-574daf7d8e41.pdf", "LOR.pdf", "application/pdf", "abhinav7bhatnagar@gmail.com", [{"email": "tech@ajuniorvc.com", "type": "fund_manager", "role": "reader"}])
        
        # print("\n=== Testing Google Sheets Reading ===\n")
        # gmail_test()

        # if test_gmail_connection("tech@ajuniorvc.com"):
        #     print("Gmail API test passed.")
        # else:
        #     print("Gmail API test failed.")
        # # Important: The service account must have access to the spreadsheet
        # try:
        #     # Get service account email to share the spreadsheet with
        #     creds = get_credentials()
        #     service_account_email = getattr(creds, 'service_account_email', 'Unknown')
        #     print(f"Using service account: {service_account_email}")
        #     print("IMPORTANT: Make sure to share the Google Sheet with this email address!\n")
            
        #     # Test reading the sheet
        #     print("Attempting to read spreadsheet...")
        #     df = read_google_sheets("https://docs.google.com/spreadsheets/d/1TO12F2cdJU17w4GQU87zTaV3FkYtemPvwdAmpnSasKQ/edit?gid=510649055#gid=510649055", "AJVC Phase 2")
        #     print("\nGoogle Sheets data:")
        #     print(df)
        # except Exception as e:
        #     print(f"Error reading Google Sheet: {e}")