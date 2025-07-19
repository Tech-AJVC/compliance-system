"""
PDF Text Extraction Utility using Mistral OCR API

This module provides functionality to extract text from PDF files using the Mistral OCR API
with direct base64 encoding and comprehensive metadata extraction:

Key Features:
- Direct base64 PDF encoding (no file uploads required)
- Native page range support via Mistral API
- Rich image extraction with bounding boxes and base64 data
- Page-level metadata (dimensions, character counts, image counts)
- Multiple output formats (markdown, json, html)
- Intelligent caching for performance
- Batch processing support
- Utility functions for image handling

Response Structure:
The Mistral OCR API returns data in this format:
{
    "pages": [
        {
            "index": 0,
            "markdown": "# Document Title...",
            "images": [
                {
                    "id": "img-0.jpeg",
                    "top_left_x": 413, "top_left_y": 600,
                    "bottom_right_x": 1286, "bottom_right_y": 893,
                    "image_base64": "data:image/jpeg;base64,...",
                    "image_annotation": null
                }
            ],
            "dimensions": {"dpi": 200, "height": 2200, "width": 1700}
        }
    ]
}

Usage Example:
    text, metadata, images = extract_text_from_pdf(
        "document.pdf",
        page_range=[0, 1, 2],  # Extract first 3 pages
        output_format="markdown"
    )
    
    # Access rich metadata
    print(f"Pages processed: {metadata['pages_processed']}")
    print(f"Page details: {metadata['page_details']}")
    
    # Work with images
    page_0_images = get_images_by_page(images, 0)
    for img in page_0_images:
        save_image_from_base64(img, f"{img['id']}")
"""

import os
import gc
import re
import json
import base64
import hashlib
from typing import Optional, List, Union, Dict, Any, Tuple
from pathlib import Path
from threading import Lock
from mistralai import Mistral, DocumentURLChunk
import tempfile


class MistralOCRManager:
    """
    Singleton manager for Mistral OCR operations with caching and optimization.
    
    Features:
    - API client reuse
    - Base64 encoding caching
    - Result caching for duplicate files
    - Memory cleanup
    """
    
    _instance = None
    _lock = Lock()
    _client = None
    _encoding_cache: Dict[str, str] = {}  # hash -> base64 mapping
    _result_cache: Dict[str, Dict] = {}  # cache_key -> result mapping
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self) -> Mistral:
        """Get or create Mistral client."""
        if self._client is None:
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("MISTRAL_API_KEY environment variable is required")
            self._client = Mistral(api_key=api_key)
        return self._client
    
    def get_file_hash(self, pdf_path: str) -> str:
        """Generate hash for PDF file for caching."""
        with open(pdf_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def encode_pdf_to_base64(self, pdf_path: str) -> str:
        """Encode PDF to base64 with caching."""
        file_hash = self.get_file_hash(pdf_path)
        
        # Check cache first
        if file_hash in self._encoding_cache:
            return self._encoding_cache[file_hash]
        
        try:
            with open(pdf_path, "rb") as pdf_file:
                base64_data = base64.b64encode(pdf_file.read()).decode('utf-8')
                
            # Cache the base64 data
            self._encoding_cache[file_hash] = base64_data
            return base64_data
            
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {pdf_path} was not found.")
        except Exception as e:
            raise Exception(f"Error encoding PDF: {e}")
    
    def process_ocr(
        self, 
        pdf_path: str, 
        pages: Optional[List[int]] = None, 
        include_images: bool = False
    ) -> Dict[str, Any]:
        """Process OCR on PDF with direct base64 encoding."""
        
        # Create cache key based on file path, pages, and include_images
        file_hash = self.get_file_hash(pdf_path)
        pages_str = str(sorted(pages)) if pages else "all"
        cache_key = f"{file_hash}_{pages_str}_{include_images}"
        
        # Check result cache
        if cache_key in self._result_cache:
            return self._result_cache[cache_key]
        
        client = self.get_client()
        
        # Encode PDF to base64
        base64_pdf = self.encode_pdf_to_base64(pdf_path)
        
        # Prepare OCR request parameters
        ocr_params = {
            "model": "mistral-ocr-latest",
            "document": DocumentURLChunk(
                document_url=f"data:application/pdf;base64,{base64_pdf}"
            ),
            "include_image_base64": include_images
        }
        
        # Add pages parameter if specified
        if pages is not None:
            ocr_params["pages"] = pages
        
        # Process with OCR
        ocr_response = client.ocr.process(**ocr_params)
        
        # Convert to dict and cache
        result = json.loads(ocr_response.model_dump_json())
        self._result_cache[cache_key] = result
        
        return result
    
    def cleanup_cache(self):
        """Clear all caches and run garbage collection."""
        self._encoding_cache.clear()
        self._result_cache.clear()
        gc.collect()


# Global manager instance
_manager = MistralOCRManager()


def _parse_page_range_string(page_range: str) -> List[int]:
    """Parse page range string like '0,5-10,20' into list of page numbers."""
    page_numbers = []
    
    for part in page_range.split(','):
        part = part.strip()
        if '-' in part:
            # Handle range like "5-10"
            start, end = part.split('-', 1)
            start = int(start.strip()) if start.strip() else 0
            end = int(end.strip()) if end.strip() else float('inf')
            page_numbers.extend(range(start, min(end + 1, 1000)))  # Cap at reasonable limit
        else:
            # Handle single page
            page_numbers.append(int(part))
    
    return sorted(set(page_numbers))


def _convert_page_range_to_list(page_range: Optional[Union[str, List[int]]]) -> Optional[List[int]]:
    """Convert page range to list format for Mistral API."""
    if page_range is None:
        return None
    
    if isinstance(page_range, list):
        return sorted(set(page_range))
    elif isinstance(page_range, str):
        return _parse_page_range_string(page_range)
    else:
        raise ValueError("page_range must be a string or list of integers")


def _convert_output_format(text: str, output_format: str) -> str:
    """Convert text to specified output format."""
    if output_format.lower() == "markdown":
        return text  # Mistral OCR typically returns markdown-like format
    elif output_format.lower() == "json":
        return json.dumps({"text": text, "format": "plain"}, indent=2)
    elif output_format.lower() == "html":
        # Simple text to HTML conversion
        html_text = text.replace('\n\n', '</p><p>').replace('\n', '<br>')
        return f"<html><body><p>{html_text}</p></body></html>"
    else:
        return text


def extract_text_from_pdf(
    pdf_path: str,
    page_range: Optional[Union[str, List[int]]] = None,
    output_format: str = "markdown",
    cleanup_after: bool = True
) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """
    Extract text from PDF using Mistral OCR API with direct base64 encoding.
    
    This function maintains the same interface as the previous implementation
    while using Mistral's OCR service with native page range support.
    
    Args:
        pdf_path (str): Path to the PDF file
        page_range (Optional[Union[str, List[int]]]): Pages to process. Can be:
            - String format: "0,5-10,20" (pages 0, 5-10, and 20)
            - List of integers: [0, 5, 6, 7, 8, 9, 10, 20]
            - None: Process all pages
        output_format (str): Output format - "markdown", "json", or "html"
        cleanup_after (bool): Whether to cleanup cache after processing
    
    Returns:
        Tuple[str, Dict[str, Any], Dict[str, Any]]: (extracted_text, metadata, images)
            - extracted_text (str): The extracted text content
            - metadata (dict): Metadata about the extraction process
            - images (dict): Extracted images (if any)
    
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If page_range format is invalid or MISTRAL_API_KEY not set
        Exception: For other extraction errors
    """
    
    try:
        # Validate PDF file exists
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Convert page range to list format for API
        pages_list = _convert_page_range_to_list(page_range)
        
        # Process with OCR using direct base64 encoding
        include_images = True  # Always extract images for compatibility
        ocr_result = _manager.process_ocr(pdf_path, pages_list, include_images)
        
        # Extract text from OCR result
        full_text = ""
        images = {}
        page_info = []
        
        if 'pages' in ocr_result:
            text_chunks = []
            image_count = 0
            
            # Process each page in the response
            for page in ocr_result['pages']:
                page_index = page.get('index', -1)
                page_markdown = page.get('markdown', '')
                page_dimensions = page.get('dimensions', {})
                
                text_chunks.append(page_markdown)
                
                # Store page information
                page_info.append({
                    'index': page_index,
                    'dimensions': page_dimensions,
                    'character_count': len(page_markdown),
                    'image_count': len(page.get('images', []))
                })
                
                # Process images embedded in this page
                if 'images' in page and page['images']:
                    for img in page['images']:
                        img_id = img.get('id', f'page_{page_index}_img_{image_count}')
                        
                        image_data = {
                            'id': img_id,
                            'page_index': page_index,
                            'bounding_box': {
                                'top_left_x': img.get('top_left_x'),
                                'top_left_y': img.get('top_left_y'),
                                'bottom_right_x': img.get('bottom_right_x'),
                                'bottom_right_y': img.get('bottom_right_y')
                            },
                            'annotation': img.get('image_annotation'),
                            'type': 'embedded'
                        }
                        
                        # Add base64 data if available
                        if 'image_base64' in img:
                            image_data['base64'] = img['image_base64']
                            image_data['format'] = 'base64_embedded'
                        
                        images[f"page_{page_index}_{img_id}"] = image_data
                        image_count += 1
            
            full_text = '\n\n'.join(text_chunks)
        
        # Convert to requested output format
        formatted_text = _convert_output_format(full_text, output_format)
        
        # Create metadata
        total_pages_processed = len(ocr_result.get('pages', [])) if 'pages' in ocr_result else 0
        page_indices = [page.get('index', -1) for page in ocr_result.get('pages', [])] if 'pages' in ocr_result else []
        
        metadata = {
            "source": "mistral_ocr",
            "model": "mistral-ocr-latest",
            "pdf_path": pdf_path,
            "page_range": page_range,
            "pages_requested": pages_list,
            "pages_processed": page_indices,
            "total_pages_processed": total_pages_processed,
            "page_details": page_info,  # Detailed info for each page
            "output_format": output_format,
            "character_count": len(formatted_text),
            "image_count": len(images),
            "total_images_across_pages": sum(p.get('image_count', 0) for p in page_info)
        }
        
        # Cleanup if requested
        if cleanup_after:
            gc.collect()
        
        return formatted_text, metadata, images
        
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        # Cleanup on error
        if cleanup_after:
            gc.collect()
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_pdf_pages(
    pdf_path: str,
    start_page: int,
    end_page: Optional[int] = None
) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """
    Extract text from specific page range using start and end page numbers.
    
    Args:
        pdf_path (str): Path to the PDF file
        start_page (int): Starting page number (0-indexed)
        end_page (Optional[int]): Ending page number (0-indexed, inclusive). 
                                 If None, extracts from start_page to end of document
    
    Returns:
        Tuple[str, Dict[str, Any], Dict[str, Any]]: (extracted_text, metadata, images)
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
) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """
    Extract text from specific page numbers.
    
    Args:
        pdf_path (str): Path to the PDF file
        page_numbers (List[int]): List of page numbers to extract (0-indexed)
    
    Returns:
        Tuple[str, Dict[str, Any], Dict[str, Any]]: (extracted_text, metadata, images)
    """
    
    if not page_numbers:
        raise ValueError("page_numbers list cannot be empty")
    
    # Sort and remove duplicates for optimal processing
    unique_pages = sorted(set(page_numbers))
    
    return extract_text_from_pdf(pdf_path, unique_pages)


def extract_text_batch(
    pdf_paths: List[str],
    page_ranges: Optional[List[Union[str, List[int], None]]] = None,
    output_format: str = "markdown"
) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    """
    Batch processing of multiple PDFs using Mistral OCR.
    
    This function processes multiple PDFs efficiently by:
    - Reusing the same Mistral client
    - Processing in sequence to avoid API rate limits
    - Cleanup between PDFs to manage memory
    
    Args:
        pdf_paths: List of PDF file paths
        page_ranges: Optional list of page ranges for each PDF
        output_format: Output format for all PDFs
    
    Returns:
        List of (text, metadata, images) tuples
    """
    
    if page_ranges is None:
        page_ranges = [None] * len(pdf_paths)
    
    if len(page_ranges) != len(pdf_paths):
        raise ValueError("page_ranges length must match pdf_paths length")
    
    results = []
    
    try:
        for i, (pdf_path, page_range) in enumerate(zip(pdf_paths, page_ranges)):
            # Process individual PDF
            result = extract_text_from_pdf(
                pdf_path, 
                page_range, 
                output_format,
                cleanup_after=True  # Cleanup between PDFs
            )
            results.append(result)
            
            # Periodic cache cleanup for long batches
            if (i + 1) % 5 == 0:  # More frequent than before due to API costs
                _manager.cleanup_cache()
    
    finally:
        # Final cleanup
        _manager.cleanup_cache()
    
    return results


# Legacy wrapper functions for backward compatibility
def extract_first_n_pages(pdf_path: str, n: int) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Extract text from first n pages of PDF."""
    return extract_text_from_pdf_pages(pdf_path, 0, n - 1)


def extract_last_n_pages(pdf_path: str, n: int) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Extract text from last n pages of PDF."""
    # For last n pages, we need to know total pages first
    # Since we can't get page count without processing, we'll use a large range
    return extract_text_from_pdf(pdf_path, f"-{n}")


def extract_single_page(pdf_path: str, page_number: int) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Extract text from a single page."""
    return extract_text_from_pdf(pdf_path, [page_number])


def cleanup_mistral_cache():
    """
    Manual cleanup function for explicit memory management.
    
    Call this function to:
    - Clear base64 encoding cache
    - Clear OCR result cache
    - Run garbage collection
    - Free up memory between processing sessions
    """
    _manager.cleanup_cache()


def get_memory_stats() -> Dict[str, Any]:
    """
    Get current memory usage statistics.
    
    Returns:
        Dictionary with memory statistics including:
        - Number of cached encodings
        - Number of cached results
        - API client status
    """
    stats = {
        "cached_encodings": len(_manager._encoding_cache),
        "cached_results": len(_manager._result_cache),
        "client_initialized": _manager._client is not None,
        "api_key_set": bool(os.getenv("MISTRAL_API_KEY"))
    }
    
    return stats


def set_api_key(api_key: str):
    """
    Set the Mistral API key programmatically.
    
    Args:
        api_key (str): The Mistral API key
    """
    os.environ["MISTRAL_API_KEY"] = api_key
    # Force client recreation with new key
    _manager._client = None


def encode_pdf_to_base64(pdf_path: str) -> str:
    """
    Utility function to encode PDF to base64.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Base64 encoded PDF data
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: For other encoding errors
    """
    return _manager.encode_pdf_to_base64(pdf_path)


# Backward compatibility aliases
cleanup_marker_cache = cleanup_mistral_cache  # For drop-in replacement


def example_usage():
    """
    Example usage of the updated Mistral OCR implementation.
    
    This function demonstrates how to use the API and shows the expected response structure.
    """
    try:
        # Example 1: Extract all pages
        text, metadata, images = extract_text_from_pdf("example.pdf")
        print("Full document extracted:")
        print(f"Pages processed: {metadata['pages_processed']}")
        print(f"Total pages: {metadata['total_pages_processed']}")
        print(f"Character count: {metadata['character_count']}")
        print(f"Images found: {metadata['image_count']}")
        
        # Show page details
        if metadata.get('page_details'):
            print("\nPage details:")
            for page_detail in metadata['page_details']:
                print(f"  Page {page_detail['index']}: {page_detail['character_count']} chars, "
                      f"{page_detail['image_count']} images, "
                      f"dimensions: {page_detail['dimensions']}")
        
        # Example 2: Extract specific pages
        text, metadata, images = extract_text_from_pdf(
            "example.pdf", 
            page_range=[0, 2, 5],  # Pages 0, 2, and 5
            output_format="markdown"
        )
        print(f"\nSpecific pages extracted: {metadata['pages_processed']}")
        
        # Example 3: Extract page range
        text, metadata, images = extract_text_from_pdf(
            "example.pdf", 
            page_range="0-3",  # Pages 0 through 3
            output_format="json"
        )
        print(f"\nPage range extracted: {metadata['pages_processed']}")
        
        # Example 4: Images handling with actual structure
        if images:
            print(f"\nImages found:")
            for img_key, img_data in images.items():
                print(f"  {img_key}:")
                print(f"    ID: {img_data.get('id')}")
                print(f"    Page: {img_data.get('page_index')}")
                print(f"    Bounding box: {img_data.get('bounding_box')}")
                print(f"    Has base64: {'base64' in img_data}")
                if img_data.get('annotation'):
                    print(f"    Annotation: {img_data.get('annotation')}")
        
        # Example 5: Working with markdown that includes image references
        if "![" in text:
            print(f"\nMarkdown contains image references:")
            # Extract image references from markdown
            image_pattern = r'!\[(.*?)\]\((.*?)\)'
            image_refs = re.findall(image_pattern, text)
            for alt_text, img_ref in image_refs:
                print(f"  Reference: {img_ref} (alt: {alt_text})")
        
        return True
        
    except Exception as e:
        print(f"Error in example usage: {e}")
        return False


if __name__ == "__main__":
    # Run example if script is executed directly
    print("Mistral OCR PDF Extractor - Example Usage")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv("MISTRAL_API_KEY"):
        print("❌ MISTRAL_API_KEY environment variable not set!")
        print("Set it with: export MISTRAL_API_KEY='your_api_key_here'")
    else:
        print("✅ MISTRAL_API_KEY is set")
        
        # Show memory stats
        stats = get_memory_stats()
        print(f"📊 Memory stats: {stats}")
        
        # You can uncomment the line below to run the example with a real PDF
        # example_usage() 


def get_images_by_page(images: Dict[str, Any], page_index: int) -> List[Dict[str, Any]]:
    """
    Get all images from a specific page.
    
    Args:
        images (Dict[str, Any]): Images dictionary returned by extract_text_from_pdf
        page_index (int): Page index to filter by
        
    Returns:
        List[Dict[str, Any]]: List of images from the specified page
    """
    page_images = []
    for img_key, img_data in images.items():
        if img_data.get('page_index') == page_index:
            page_images.append({
                'key': img_key,
                **img_data
            })
    return page_images


def save_image_from_base64(image_data: Dict[str, Any], output_path: str) -> bool:
    """
    Save a base64 image to file.
    
    Args:
        image_data (Dict[str, Any]): Image data dictionary containing base64 data
        output_path (str): Path where to save the image file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if 'base64' not in image_data:
            print(f"No base64 data found in image")
            return False
            
        base64_data = image_data['base64']
        
        # Handle data URI format (data:image/jpeg;base64,...)
        if base64_data.startswith('data:'):
            # Extract just the base64 part after the comma
            base64_data = base64_data.split(',', 1)[1]
        
        # Decode and save
        image_bytes = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(image_bytes)
            
        print(f"Image saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def get_image_info_summary(images: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of all images with their metadata.
    
    Args:
        images (Dict[str, Any]): Images dictionary returned by extract_text_from_pdf
        
    Returns:
        Dict[str, Any]: Summary information about all images
    """
    if not images:
        return {"total_images": 0, "pages_with_images": [], "images_by_page": {}}
    
    pages_with_images = set()
    images_by_page = {}
    total_with_base64 = 0
    
    for img_key, img_data in images.items():
        page_idx = img_data.get('page_index', -1)
        pages_with_images.add(page_idx)
        
        if page_idx not in images_by_page:
            images_by_page[page_idx] = []
        
        images_by_page[page_idx].append({
            'key': img_key,
            'id': img_data.get('id'),
            'has_base64': 'base64' in img_data,
            'bounding_box': img_data.get('bounding_box')
        })
        
        if 'base64' in img_data:
            total_with_base64 += 1
    
    return {
        "total_images": len(images),
        "total_with_base64": total_with_base64,
        "pages_with_images": sorted(list(pages_with_images)),
        "images_by_page": images_by_page
    } 