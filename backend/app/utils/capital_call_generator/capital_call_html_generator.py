"""
Capital Call Notice Generator - HTML to PDF Version using Jinja2 templates
"""
import os
import base64
from pathlib import Path
from jinja2 import Template
from datetime import datetime
import logging
from typing import Dict, Any

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    logging.warning("pdfkit not available. HTML to PDF conversion will not work.")

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logging.warning("weasyprint not available. Using pdfkit as fallback.")

logger = logging.getLogger(__name__)

def get_logo_base64(logo_path: str = "images_docs/ajvc_logo.png") -> str:
    """
    Convert AJVC logo to base64 for embedding in HTML
    
    Args:
        logo_path: Path to the logo file
        
    Returns:
        Base64 encoded logo string or empty string if file not found
    """
    try:
        # Get the absolute path relative to backend directory
        # From backend/app/utils/capital_call_generator/ go 4 levels up to get to backend/
        backend_dir = Path(__file__).parent.parent.parent.parent
        full_logo_path = backend_dir / logo_path
        
        if full_logo_path.exists():
            with open(full_logo_path, "rb") as logo_file:
                logo_data = logo_file.read()
                logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                return f"data:image/png;base64,{logo_base64}"
        else:
            logger.warning(f"Logo file not found at: {full_logo_path}")
            return ""
    except Exception as e:
        logger.error(f"Error loading logo: {e}")
        return ""

# HTML Template for Capital Call Notice - Enhanced for PDF Generation
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&display=swap');
        
        @page {
            size: A4;
            margin: 0.75in;
        }
        
        body { 
            font-family: 'Calibri', 'Arial', sans-serif; 
            font-size: 11pt;
            line-height: 1.3;
            color: #000;
            margin: 0;
            padding: 0;
        }
        
        .logo-section { 
            margin-bottom: 30px;
            display: flex;
            align-items: center;
        }
        
        .logo-image {
            height: 50px;
            width: auto;
            margin-right: 10px;
        }
        
        .logo-text { 
            color: #d32f2f; 
            font-size: 16pt; 
            font-weight: bold; 
            font-family: 'Calibri', 'Arial', sans-serif;
        }
        
        .header { 
            color: #d32f2f; 
            font-size: 30pt; 
            font-weight: 700; 
            margin-bottom: 25px;
            font-family: 'Bricolage Grotesque', 'Calibri', 'Arial', sans-serif;
        }
        
        .notice-investor-table { 
            width: 100%; 
            margin: 20px 0; 
            border-collapse: collapse;
            font-size: 11pt;
        }
        
        .notice-investor-table td { 
            padding: 3px 0; 
            vertical-align: top;
        }
        
        .notice-investor-table .label { 
            font-weight: bold; 
            width: 200px;
        }
        
        .notice-investor-table .spacer-col {
            width: 100px;
        }
        
        .content-text {
            margin: 12px 0;
            font-size: 11pt;
            line-height: 1.3;
        }
        
        .bank-details {
            margin: 15px 0;
            font-size: 11pt;
        }
        
        .bank-details-table {
            border-collapse: collapse;
            margin: 10px 0;
        }
        
        .bank-details-table td {
            padding: 2px 0;
            vertical-align: top;
        }
        
        .bank-details-table .label {
            font-weight: bold;
            width: 120px;
            padding-right: 10px;
        }
        
        .summary-table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0; 
            max-width: 450px;
            font-size: 11pt;
        }
        
        .summary-table th, .summary-table td { 
            border: 1px solid #000; 
            padding: 8px; 
            text-align: left; 
        }
        
        .summary-table th { 
            background-color: #f5f5f5; 
            font-weight: bold;
        }
        
        .summary-table .amount-col { 
            text-align: right; 
            width: 120px;
        }
        
        .final-instructions {
            margin: 20px 0;
            font-size: 11pt;
            line-height: 1.3;
        }
        
        .bold {
            font-weight: bold;
        }
        
        /* Specific styling to match the Capital Call image */
        .wire-instructions {
            margin-top: 10px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="logo-section">
        {% if logo_base64 %}
        <img src="{{ logo_base64 }}" alt="AJVC Logo" class="logo-image">
        {% endif %}
    </div>
    
    <div class="header">Capital Call</div>
    
    <table class="notice-investor-table">
        <tr>
            <td class="label">Notice date</td>
            <td class="spacer-col"></td>
            <td class="label">Investor</td>
        </tr>
        <tr>
            <td>{{ notice_date }}</td>
            <td></td>
            <td>{{ investor }}</td>
        </tr>
    </table>
    
    <div class="content-text">
        <p>Dear {{ investor }},</p>
        
        <p>Thank you for being AJVC's first supporters as we begin this journey. We are grateful for your support from Day 1.</p>
        
        <p>We are writing to notify you, as per the Contribution Agreement entered with AJVC Fund.</p>
        
        <p>The Fund is calling capital from you in the amount of INR {{ "{:,}".format(amount_due) }} - which is {{ ((amount_due / total_commitment) * 100) | round | int }}% of your committed capital.</p>
        
        <p>Contribution is due on or before {{ contribution_due_date }} and must be wired in immediately.</p>
        
        <p class="wire-instructions">The wire instructions are as follows:</p>
    </div>
    
    <div class="bank-details">
        <table class="bank-details-table">
            <tr>
                <td class="label">Bank Name:</td>
                <td>{{ bank_name }}</td>
            </tr>
            <tr>
                <td class="label">IFSC:</td>
                <td>{{ ifsc }}</td>
            </tr>
            <tr>
                <td class="label">Acct Name:</td>
                <td>{{ acct_name }}</td>
            </tr>
            <tr>
                <td class="label">Acct Number:</td>
                <td>{{ acct_number }}</td>
            </tr>
            <tr>
                <td class="label">Bank Contact:</td>
                <td>{{ bank_contact }}</td>
            </tr>
            <tr>
                <td class="label">Phone:</td>
                <td>{{ phone }}</td>
            </tr>
        </table>
    </div>
    
    <table class="summary-table">
        <tr>
            <th>Investor Commitment Summary</th>
            <th class="amount-col">Amount</th>
        </tr>
        <tr>
            <td>Total commitment</td>
            <td class="amount-col">₹ {{ "{:,}".format(total_commitment) }}</td>
        </tr>
        <tr>
            <td>Amount called-up and paid till date</td>
            <td class="amount-col">₹ {{ "{:,}".format(amount_called_up) }}</td>
        </tr>
        <tr>
            <td>Remaining commitment after this drawdown</td>
            <td class="amount-col">₹ {{ "{:,}".format(remaining_commitment) }}</td>
        </tr>
        <tr>
            <td class="bold">Amount due</td>
            <td class="amount-col bold">₹ {{ "{:,}".format(amount_due) }}</td>
        </tr>
    </table>
    
    <div class="final-instructions">
        <p>Please instruct the financial institution ({{ bank_name }}) handling the wire transfer to include your name, as a Limited Partner of the Fund.</p>
        
        <p>We plan to do quarterly drawdowns at the beginning of each quarter.<br>
        <span class="bold">Forecasted next quarter ({{ forecast_next_quarter_period }}) drawdown: {{ forecast_next_quarter }}% of the committed amount.</span></p>
    </div>
</body>
</html>
"""

class CapitalCallHTMLGenerator:
    def __init__(self, output_dir: str = "uploads/capital_calls"):
        """
        Initialize the HTML to PDF generator
        
        Args:
            output_dir: Directory to save generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template = Template(HTML_TEMPLATE)
    
    def generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate HTML content from template and data
        
        Args:
            data: Dictionary containing all the dynamic data
            
        Returns:
            HTML content as string
        """
        # Add logo to template data
        template_data = data.copy()
        template_data['logo_base64'] = get_logo_base64()
        
        return self.template.render(**template_data)
    
    def generate_capital_call_html_file(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Generate capital call notice as HTML file
        
        Args:
            data: Dictionary containing all the dynamic data for the template
            filename: Optional custom filename
            
        Returns:
            Path to the generated HTML file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capital_call_{data.get('investor', 'unknown').replace(' ', '_')}_{timestamp}.html"
        
        html_content = self.generate_html(data)
        
        file_path = self.output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML capital call notice: {file_path}")
        return str(file_path)
    
    def generate_capital_call_pdf_from_html(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Generate capital call notice as PDF from HTML template
        
        Args:
            data: Dictionary containing all the dynamic data for the template
            filename: Optional custom filename
            
        Returns:
            Path to the generated PDF file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capital_call_{data.get('investor', 'unknown').replace(' ', '_')}_{timestamp}.pdf"
        
        html_content = self.generate_html(data)
        file_path = self.output_dir / filename
        
        # Try WeasyPrint first (better CSS support), then pdfkit
        if WEASYPRINT_AVAILABLE:
            try:
                weasyprint.HTML(string=html_content).write_pdf(str(file_path))
                logger.info(f"Generated PDF capital call notice using WeasyPrint: {file_path}")
                return str(file_path)
            except Exception as e:
                logger.warning(f"WeasyPrint failed: {e}. Trying pdfkit...")
        
        if PDFKIT_AVAILABLE:
            try:
                # Configure pdfkit options for better output
                options = {
                    'page-size': 'A4',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': "UTF-8",
                    'no-outline': None
                }
                pdfkit.from_string(html_content, str(file_path), options=options)
                logger.info(f"Generated PDF capital call notice using pdfkit: {file_path}")
                return str(file_path)
            except Exception as e:
                logger.error(f"pdfkit failed: {e}")
                raise Exception("Failed to generate PDF. Please install wkhtmltopdf or weasyprint.")
        
        raise Exception("No PDF generation library available. Please install pdfkit or weasyprint.")

def generate_capital_call_html(data: Dict[str, Any], output_path: str = None, pdf: bool = True) -> str:
    """
    Convenience function to generate capital call PDF (default) or HTML
    
    Args:
        data: Dictionary containing all the dynamic data
        output_path: Optional output path
        pdf: If True, generate PDF (default); if False, generate HTML
        
    Returns:
        Path to generated file
    """
    generator = CapitalCallHTMLGenerator()
    
    if output_path:
        filename = Path(output_path).name
    else:
        filename = None
    
    if pdf:
        return generator.generate_capital_call_pdf_from_html(data, filename)
    else:
        return generator.generate_capital_call_html_file(data, filename)

def generate_capital_call_pdf(data: Dict[str, Any], output_path: str = None) -> str:
    """
    Direct function to generate capital call PDF using HTML template
    
    Args:
        data: Dictionary containing all the dynamic data
        output_path: Optional output path
        
    Returns:
        Path to generated PDF file
    """
    return generate_capital_call_html(data, output_path, pdf=True)