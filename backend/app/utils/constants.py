"""
Constants for LP document processing and page extraction
"""

# Page ranges for different document types (0-indexed)
DOCUMENT_PAGE_RANGES = {
    "CONTRIBUTION_AGREEMENT": [4, 62, 63],  # Pages to extract from Contribution Agreement
    "CML": [0,1],  # Pages to extract from Client Master List
    "KYC": []  # KYC documents don't need specific page extraction
}

# Document types for identification
DOCUMENT_TYPES = {
    "KYC": "KYC",
    "CONTRIBUTION_AGREEMENT": "Contribution Agreement", 
    "CML": "CML",
    "DRAWDOWN_NOTICE": "Drawdown Notice"
}

# Document type identification keywords
DOCUMENT_KEYWORDS = {
    "KYC": ["kyc", "know your customer", "customer due diligence"],
    "CONTRIBUTION_AGREEMENT": ["contribution agreement", "subscription agreement", "capital commitment", "CA"],
    "CML": ["client master list", "cml", "master list"],
    "DRAWDOWN_NOTICE": ["drawdown notice", "capital call", "drawdown", "notice", "funding notice"]
}

# LP status values
LP_STATUS = {
    "WAITING_FOR_KYC": "Waiting for KYC",
    "CML_PENDING": "CML Pending", 
    "ACTIVE": "Active"
}

# MIME types for supported documents
SUPPORTED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
} 