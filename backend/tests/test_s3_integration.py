#!/usr/bin/env python3
"""
Test script for S3 integration with capital call PDFs
"""
import sys
import os
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.utils.s3_storage import S3DocumentStorage
from app.utils.capital_call_generator.capital_call_html_generator import generate_capital_call_pdf

def test_s3_integration():
    """Test S3 integration with capital call PDF generation"""
    
    print("Testing S3 Integration with Capital Call PDFs")
    print("=" * 50)
    
    # Sample data for capital call PDF
    sample_data = {
        'notice_date': '2025-01-15',
        'investor': 'Warren Buffet',
        'amount_due': 50000.00,
        'total_commitment': 200000.00,
        'amount_called_up': 75000.00,
        'remaining_commitment': 125000.00,
        'contribution_due_date': '2025-02-15',
        'bank_name': 'AJVC Bank',
        'ifsc': 'AJVC0001234',
        'acct_name': 'AJVC Fund Account',
        'acct_number': '1234567890',
        'bank_contact': 'John Smith',
        'phone': '+91-9876543210',
        'forecast_next_quarter': 25.0,
        'forecast_next_quarter_period': "Q2'25"
    }
    
    try:
        # Step 1: Generate PDF locally
        print("Step 1: Generating PDF locally...")
        pdf_path = generate_capital_call_pdf(sample_data)
        print(f"✓ PDF generated successfully at: {pdf_path}")
        
        # Step 2: Test S3 connection (will fail gracefully if not configured)
        print("\nStep 2: Testing S3 upload...")
        try:
            from datetime import datetime
            s3_storage = S3DocumentStorage()
            
            # Create folder structure: Fund Scheme/Quarter/Capital Calls/lp_name_timestamp.pdf
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fund_name = "AJVC_Fund_I"
            quarter = "Q1'25"
            lp_name = "Warren_Buffet"
            
            s3_key = f"{fund_name}/{quarter}/Capital Calls/{lp_name}_{timestamp}.pdf"
            
            metadata = {
                'document_type': 'capital_call',
                'quarter': quarter,
                'lp_name': 'Warren Buffet',
                'fund_name': 'AJVC Fund I',
                'test_upload': 'true',
                'generated_by': 'test_script'
            }
            
            # Upload using generic upload_file function
            upload_result = s3_storage.upload_file(
                local_file_path=pdf_path,
                s3_key=s3_key,
                metadata=metadata,
                content_type='application/pdf'
            )
            
            if upload_result['success']:
                print(f"✓ PDF uploaded successfully to S3:")
                print(f"  S3 Key: {upload_result['s3_key']}")
                print(f"  S3 URL: {upload_result['s3_url']}")
                print(f"  Folder Structure: {fund_name}/{quarter}/Capital Calls/")
                print(f"  Filename: {lp_name}_{timestamp}.pdf")
            else:
                print(f"✗ S3 upload failed: {upload_result.get('error', 'Unknown error')}")
                
        except Exception as s3_error:
            print(f"✗ S3 not configured or error: {str(s3_error)}")
            print("  This is expected if S3 credentials are not set up.")
        
        # Step 3: Test list objects with limit
        print("\nStep 3: Testing list objects...")
        try:
            s3_storage = S3DocumentStorage()
            
            # Test listing objects from different prefixes
            test_prefixes = ["", "AJVC_Fund_I/", "AJVC_Fund_I/Q1'25/", "AJVC_Fund_I/Q1'25/Capital Calls/"]
            for prefix in test_prefixes:
                objects = s3_storage.list_objects(prefix=prefix, limit=5)
                print(f"  Prefix '{prefix}': Found {len(objects)} objects (limit: 5)")
                
        except Exception as list_error:
            print(f"✗ List objects test failed: {str(list_error)}")
        
        print("\n" + "=" * 50)
        print("Test completed! Check the generated PDF and S3 configuration.")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_s3_integration()
    sys.exit(0 if success else 1)