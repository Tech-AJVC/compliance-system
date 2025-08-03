"""
Capital Call Notice Generator - PDF Version using reportlab
"""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CapitalCallPDFGenerator:
    def __init__(self, output_dir: str = "uploads/capital_calls"):
        """
        Initialize the PDF generator
        
        Args:
            output_dir: Directory to save generated PDF files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_capital_call_pdf(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Generate capital call notice as PDF file
        
        Args:
            data: Dictionary containing all the dynamic data for the template
            filename: Optional custom filename
            
        Returns:
            Path to the generated PDF file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capital_call_{data.get('investor', 'unknown').replace(' ', '_')}_{timestamp}.pdf"
        
        file_path = self.output_dir / filename
        doc = SimpleDocTemplate(str(file_path), pagesize=A4)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.red,
            spaceAfter=30,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12
        )
        
        # Add AJVC logo placeholder
        logo_para = Paragraph('<font size="16" color="red"><b>AJVC</b></font>', normal_style)
        story.append(logo_para)
        story.append(Spacer(1, 20))
        
        # Title
        title = Paragraph("Capital Call", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Notice date and investor in table format
        header_data = [
            ['<b>Notice date</b>', '', '<b>Investor</b>'],
            [data.get('notice_date', ''), '', data.get('investor', '')]
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 2*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Personal message
        message_parts = [
            f"Dear {data.get('investor', '')},",
            "",
            "Thank you for being AJVC's first supporters as we begin this journey. We are grateful for your support from Day 1.",
            "",
            "We are writing to notify you, as per the Contribution Agreement entered with AJVC Fund.",
            "",
            f"The Fund is calling capital from you in the amount of INR {data.get('amount_due', 0):,} - which is {(data.get('amount_due', 0)/data.get('total_commitment', 1)*100):.0f}% of your committed capital.",
            "",
            f"Contribution is due on or before {data.get('contribution_due_date', '')} and must be wired in immediately.",
            "",
            "The wire instructions are as follows:"
        ]
        
        for part in message_parts:
            if part == "":
                story.append(Spacer(1, 6))
            else:
                para = Paragraph(part, normal_style)
                story.append(para)
        
        # Bank details table
        bank_data = [
            ['<b>Bank Name:</b>', data.get('bank_name', '')],
            ['<b>IFSC:</b>', data.get('ifsc', '')],
            ['<b>Acct Name:</b>', data.get('acct_name', '')],
            ['<b>Acct Number:</b>', data.get('acct_number', '')],
            ['<b>Bank Contact:</b>', data.get('bank_contact', '')],
            ['<b>Phone:</b>', data.get('phone', '')]
        ]
        
        bank_table = Table(bank_data, colWidths=[1.5*inch, 3*inch])
        bank_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(bank_table)
        story.append(Spacer(1, 20))
        
        # Commitment summary table
        summary_data = [
            ['<b>Investor Commitment Summary</b>', '<b>Amount</b>'],
            ['Total commitment', f'₹ {data.get("total_commitment", 0):,}'],
            ['Amount called-up and paid till date', f'₹ {data.get("amount_called_up", 0):,}'],
            ['Remaining commitment after this drawdown', f'₹ {data.get("remaining_commitment", 0):,}'],
            ['Amount due', f'₹ {data.get("amount_due", 0):,}']
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Final instructions
        final_parts = [
            f"Please instruct the financial institution ({data.get('bank_name', '')}) handling the wire transfer to include your name, as a Limited Partner of the Fund.",
            "",
            "We plan to do quarterly drawdowns at the beginning of each quarter.",
            f"Forecasted next quarter ({data.get('forecast_next_quarter_period', '')}) drawdown: {data.get('forecast_next_quarter', 0):.0f}% of the committed amount."
        ]
        
        for part in final_parts:
            if part == "":
                story.append(Spacer(1, 6))
            else:
                para = Paragraph(part, normal_style)
                story.append(para)
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Generated PDF capital call notice: {file_path}")
        return str(file_path)

def generate_capital_call_pdf(data: Dict[str, Any], output_path: str = None) -> str:
    """
    Convenience function to generate capital call PDF
    
    Args:
        data: Dictionary containing all the dynamic data
        output_path: Optional output path
        
    Returns:
        Path to generated file
    """
    generator = CapitalCallPDFGenerator()
    
    if output_path:
        filename = Path(output_path).name
    else:
        filename = None
        
    return generator.generate_capital_call_pdf(data, filename)