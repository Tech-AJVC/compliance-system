"""
Test script for Google Drive file upload with sharing.
"""
import os
import sys
from backend.app.utils.google_clients_gcp import drive_file_dump

def test_drive_upload_with_sharing():
    # Path to a test PDF file (create one if it doesn't exist)
    test_file_path = "test_upload.pdf"
    
    # Create a simple test PDF if it doesn't exist
    if not os.path.exists(test_file_path):
        try:
            # Try to create a simple PDF using reportlab
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(test_file_path)
            c.drawString(100, 750, "Test PDF for Google Drive Upload")
            c.save()
            print(f"Created test PDF file: {test_file_path}")
        except ImportError:
            # If reportlab is not installed, create a text file and rename it
            with open(test_file_path, "w") as f:
                f.write("This is a test file for Google Drive upload.")
            print(f"Created test file: {test_file_path}")
    
    # Your email address to share the file with
    your_email = input("Enter your email address to share the file with: ")
    
    # Upload the file to Google Drive and share it
    result = drive_file_dump(
        file_path=test_file_path,
        file_name="Test Upload.pdf",
        mime_type="application/pdf",
        share_with_email=your_email
    )
    
    if result:
        print("\nFile upload successful!")
        print(f"File ID: {result.get('id')}")
        print(f"File Name: {result.get('name')}")
        print(f"Web View Link: {result.get('webViewLink')}")
        print(f"\nCheck your email ({your_email}) for the sharing notification.")
        print("You should now be able to access this file in your Google Drive.")
    else:
        print("File upload failed.")

if __name__ == "__main__":
    test_drive_upload_with_sharing()
