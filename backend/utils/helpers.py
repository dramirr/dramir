"""
Helper Utilities
"""
import re
import hashlib
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def convert_persian_to_english_numbers(text: str) -> str:
    """
    Convert Persian/Arabic numbers to English
    
    Args:
        text: Text containing Persian/Arabic numbers
        
    Returns:
        Text with English numbers
    """
    if not text:
        return text
    
    persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    
    text = text.translate(persian_to_english)
    text = text.translate(arabic_to_english)
    
    return text


def normalize_arabic_to_persian(text: str) -> str:
    """
    Convert Arabic characters to Persian
    
    Args:
        text: Text with Arabic characters
        
    Returns:
        Text with Persian characters
    """
    if not text:
        return text
    
    arabic_to_persian = str.maketrans('يك', 'یک')
    return text.translate(arabic_to_persian)


def format_phone_number(phone: str) -> str:
    """
    Format phone number for display
    
    Args:
        phone: Raw phone number
        
    Returns:
        Formatted phone number (e.g., 0912 345 6789)
    """
    if not phone:
        return ''
    
    phone = re.sub(r'[^0-9]', '', phone)
    
    if len(phone) == 11 and phone.startswith('09'):
        return f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    
    return phone


def generate_unique_filename(original_filename: str, prefix: Optional[str] = None) -> str:
    """
    Generate unique filename
    
    Args:
        original_filename: Original filename
        prefix: Optional prefix
        
    Returns:
        Unique filename with timestamp
    """
    from werkzeug.utils import secure_filename
    
    filename = secure_filename(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    
    if prefix:
        return f"{prefix}_{timestamp}_{filename}"
    else:
        return f"{timestamp}_{filename}"


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of file
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex digest of file hash
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {str(e)}")
        return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size for display
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size (e.g., "2.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_numbers_from_text(text: str) -> list:
    """
    Extract all numbers from text
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of numbers found
    """
    if not text:
        return []
    
    text = convert_persian_to_english_numbers(text)
    
    numbers = re.findall(r'\d+(?:\.\d+)?', text)
    
    return [float(n) if '.' in n else int(n) for n in numbers]


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ''
    
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()