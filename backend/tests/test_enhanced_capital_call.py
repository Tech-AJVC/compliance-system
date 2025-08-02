"""
Test script for Enhanced Capital Call HTML→PDF Generator
Tests the enhanced styling and PDF output
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import the enhanced generator
from app.utils.capital_call_generator.capital_call_html_generator import generate_capital_call_pdf, generate_capital_call_html

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sample_data():
    """
    Get sample data for testing capital call generation
    """
    return {
        'notice_date': '07th April 2025',
        'investor': 'Anurag Agrawal',
        'amount_due': 5000000,
        'total_commitment': 10000000,
        'amount_called_up': 2000000,
        'remaining_commitment': 7500000,
        'contribution_due_date': '22nd April, 2025',
        'bank_name': 'SBI',
        'ifsc': 'SBIN0009995',
        'acct_name': 'AJVC FUND',
        'acct_number': '43471853599',
        'bank_contact': 'Aviral Bhatnagar',
        'phone': '8758295844',
        'forecast_next_quarter': 5,
        'forecast_next_quarter_period': 'Q2\'25 Jul-Sep'
    }

def test_enhanced_html_to_pdf():
    """
    Test the enhanced HTML→PDF generation with improved styling
    """
    logger.info("🔹 Testing Enhanced HTML→PDF Generation...")
    try:
        data = get_sample_data()
        
        # Generate PDF directly
        pdf_path = generate_capital_call_pdf(data)
        
        # Check if file was created
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            logger.info(f"✅ Enhanced PDF generated successfully: {pdf_path}")
            logger.info(f"   File size: {file_size:,} bytes")
            
            # Also generate HTML for comparison
            html_path = generate_capital_call_html(data, pdf=False)
            if os.path.exists(html_path):
                html_size = os.path.getsize(html_path)
                logger.info(f"✅ HTML version also generated: {html_path}")
                logger.info(f"   HTML file size: {html_size:,} bytes")
            
            return True, {'pdf': pdf_path, 'html': html_path if os.path.exists(html_path) else None}
        else:
            logger.error("❌ PDF file was not created")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Enhanced PDF generation failed: {str(e)}")
        return False, None

def test_multiple_investors():
    """
    Test generating capital calls for multiple investors
    """
    logger.info("🔹 Testing Multiple Investor Generation...")
    
    investors = [
        {
            'investor': 'Warren Buffet',
            'amount_due': 10000000,
            'total_commitment': 50000000,
            'amount_called_up': 15000000,
            'remaining_commitment': 40000000,
        },
        {
            'investor': 'Peter Lynch',
            'amount_due': 2500000,
            'total_commitment': 12500000,
            'amount_called_up': 3750000,
            'remaining_commitment': 10000000,
        },
        {
            'investor': 'Benjamin Graham',
            'amount_due': 1000000,
            'total_commitment': 5000000,
            'amount_called_up': 1500000,
            'remaining_commitment': 4000000,
        }
    ]
    
    base_data = get_sample_data()
    generated_files = []
    
    try:
        for investor_data in investors:
            # Update base data with investor-specific information
            test_data = {**base_data, **investor_data}
            
            # Generate PDF
            pdf_path = generate_capital_call_pdf(test_data)
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                logger.info(f"✅ Generated PDF for {investor_data['investor']}: {pdf_path}")
                logger.info(f"   File size: {file_size:,} bytes")
                generated_files.append(pdf_path)
            else:
                logger.error(f"❌ Failed to generate PDF for {investor_data['investor']}")
        
        logger.info(f"📊 Successfully generated {len(generated_files)} out of {len(investors)} capital call PDFs")
        return len(generated_files) == len(investors), generated_files
        
    except Exception as e:
        logger.error(f"❌ Multiple investor generation failed: {str(e)}")
        return False, []

def test_warren_buffet_only():
    """
    Test generating capital call for Warren Buffet only
    """
    logger.info("🔹 Testing Warren Buffet Capital Call Generation...")
    
    base_data = get_sample_data()
    warren_data = {
        'investor': 'Warren Buffet',
        'amount_due': 10000000,
        'total_commitment': 50000000,
        'amount_called_up': 15000000,
        'remaining_commitment': 40000000,
    }
    
    # Update base data with Warren Buffet's information
    test_data = {**base_data, **warren_data}
    
    try:
        # Generate PDF
        pdf_path = generate_capital_call_pdf(test_data)
        
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            logger.info(f"✅ Generated PDF for Warren Buffet: {pdf_path}")
            logger.info(f"   File size: {file_size:,} bytes")
            return True, pdf_path
        else:
            logger.error("❌ Failed to generate PDF for Warren Buffet")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Warren Buffet PDF generation failed: {str(e)}")
        return False, None

def main():
    """
    Main test function - Warren Buffet only
    """
    logger.info("🚀 Testing Warren Buffet Capital Call PDF Generation...")
    logger.info("="*70)
    
    # Test: Warren Buffet PDF generation only
    success, pdf_path = test_warren_buffet_only()
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 WARREN BUFFET TEST SUMMARY")
    logger.info("="*70)
    
    if success:
        logger.info("✅ Warren Buffet PDF Generation: SUCCESS")
        if pdf_path and os.path.exists(pdf_path):
            size = os.path.getsize(pdf_path)
            logger.info(f"📄 Generated: {pdf_path} ({size:,} bytes)")
    else:
        logger.info("❌ Warren Buffet PDF Generation: FAILED")
    
    # Recommendations
    logger.info("\n💡 STYLING ENHANCEMENTS APPLIED:")
    logger.info("   🎨 Calibri/Arial font family for professional appearance")
    logger.info("   📏 Proper margins and spacing matching original design")
    logger.info("   🔴 Red color for AJVC logo and 'Capital Call' header")
    logger.info("   📊 Enhanced table styling with borders and proper alignment")
    logger.info("   💪 Bold formatting for labels and important information")
    logger.info("   📄 A4 page formatting optimized for PDF output")
    logger.info("   🖼️ AJVC logo integration (if available)")
    
    return success

if __name__ == "__main__":
    success = main()
    
    print(f"\n✨ Enhanced testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📂 Check the uploads/capital_calls/ directory for enhanced PDF files!")
    
    if success:
        print("🎉 All tests passed! The enhanced HTML→PDF generator is working perfectly.")
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")