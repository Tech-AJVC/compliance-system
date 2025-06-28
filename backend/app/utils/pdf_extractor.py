"""
PDF Text Extraction Utility using Marker

This module provides functionality to extract text from PDF files using the marker library
with support for specifying page ranges.
"""

from typing import Optional, List, Union
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser


def extract_text_from_pdf(
    pdf_path: str,
    page_range: Optional[Union[str, List[int]]] = None,
    output_format: str = "markdown"
) -> tuple[str, dict, dict]:
    """
    Extract text from PDF using marker library with optional page range specification.
    
    Args:
        pdf_path (str): Path to the PDF file
        page_range (Optional[Union[str, List[int]]]): Pages to process. Can be:
            - String format: "0,5-10,20" (pages 0, 5-10, and 20)
            - List of integers: [0, 5, 6, 7, 8, 9, 10, 20]
            - None: Process all pages
        output_format (str): Output format - "markdown", "json", or "html"
    
    Returns:
        tuple: (extracted_text, metadata, images)
            - extracted_text (str): The extracted text content
            - metadata (dict): Metadata about the extraction process
            - images (dict): Extracted images (if any)
    
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If page_range format is invalid
        Exception: For other extraction errors
    """
    
    try:
        # Prepare configuration
        config = {
            "output_format": output_format
        }
        
        # Add page range if specified
        if page_range is not None:
            if isinstance(page_range, list):
                # Convert list to comma-separated string
                page_range_str = ",".join(map(str, page_range))
            elif isinstance(page_range, str):
                page_range_str = page_range
            else:
                raise ValueError("page_range must be a string or list of integers")
            
            config["page_range"] = page_range_str
        
        # Create config parser
        config_parser = ConfigParser(config)
        
        # Initialize the PDF converter with configuration
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer()
        )
        
        # Convert the PDF
        rendered = converter(pdf_path)
        
        # Extract text and metadata
        text, metadata, images = text_from_rendered(rendered)
        
        return text, metadata, images
        
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_pdf_pages(
    pdf_path: str,
    start_page: int,
    end_page: Optional[int] = None
) -> tuple[str, dict, dict]:
    """
    Extract text from specific page range using start and end page numbers.
    
    Args:
        pdf_path (str): Path to the PDF file
        start_page (int): Starting page number (0-indexed)
        end_page (Optional[int]): Ending page number (0-indexed, inclusive). 
                                 If None, extracts from start_page to end of document
    
    Returns:
        tuple: (extracted_text, metadata, images)
    """
    
    if end_page is not None:
        if end_page < start_page:
            raise ValueError("end_page must be greater than or equal to start_page")
        page_range = f"{start_page}-{end_page}"
    else:
        page_range = f"{start_page}-"
    
    return extract_text_from_pdf(pdf_path, page_range)


def extract_text_from_specific_pages(
    pdf_path: str,
    page_numbers: List[int]
) -> tuple[str, dict, dict]:
    """
    Extract text from specific page numbers.
    
    Args:
        pdf_path (str): Path to the PDF file
        page_numbers (List[int]): List of page numbers to extract (0-indexed)
    
    Returns:
        tuple: (extracted_text, metadata, images)
    """
    
    if not page_numbers:
        raise ValueError("page_numbers list cannot be empty")
    
    # Sort and remove duplicates
    unique_pages = sorted(set(page_numbers))
    
    return extract_text_from_pdf(pdf_path, unique_pages)


# Example usage functions for common scenarios
def extract_first_n_pages(pdf_path: str, n: int) -> tuple[str, dict, dict]:
    """Extract text from first n pages of PDF."""
    return extract_text_from_pdf_pages(pdf_path, 0, n - 1)


def extract_last_n_pages(pdf_path: str, n: int) -> tuple[str, dict, dict]:
    """
    Extract text from last n pages of PDF.
    Note: This requires knowing the total page count first.
    """
    # For this implementation, we'll extract all pages and let marker handle it
    # In a production environment, you might want to get page count first
    return extract_text_from_pdf(pdf_path, f"-{n}")


def extract_single_page(pdf_path: str, page_number: int) -> tuple[str, dict, dict]:
    """Extract text from a single page."""
    return extract_text_from_pdf(pdf_path, str(page_number)) 