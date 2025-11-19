"""
Candidate Deduplication Service
"""
import re
import logging
from typing import Optional

from backend.database.db import get_db_session
from backend.database.models import Candidate

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to standard format
    
    Args:
        phone: Raw phone number
        
    Returns:
        Normalized phone number (11 digits starting with 09)
    """
    if not phone:
        return None
    
    phone = str(phone).strip()
    
    phone = re.sub(r'[^0-9]', '', phone)
    
    persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    phone = phone.translate(persian_to_english)
    
    if phone.startswith('0098'):
        phone = '0' + phone[4:]
    elif phone.startswith('98'):
        phone = '0' + phone[2:]
    elif phone.startswith('+98'):
        phone = '0' + phone[3:]
    elif not phone.startswith('0'):
        phone = '0' + phone
    
    if not (phone.startswith('09') and len(phone) == 11):
        logger.warning(f"Invalid phone format after normalization: {phone}")
    
    return phone


def find_by_phone(phone: str) -> Optional[Candidate]:
    """
    Find candidate by phone number
    
    Args:
        phone: Phone number to search
        
    Returns:
        Candidate object if found, None otherwise
    """
    if not phone:
        return None
    
    normalized = normalize_phone(phone)
    
    if not normalized:
        return None
    
    try:
        with get_db_session() as db:
            candidate = db.query(Candidate).filter_by(phone=normalized).first()
            return candidate
    except Exception as e:
        logger.error(f"Error finding candidate by phone: {str(e)}")
        return None


def find_duplicates() -> list:
    """
    Find all candidates with multiple resume submissions
    
    Returns:
        List of candidates with submission count > 1
    """
    try:
        with get_db_session() as db:
            candidates = db.query(Candidate)\
                .filter(Candidate.total_submissions > 1)\
                .order_by(Candidate.total_submissions.desc())\
                .all()
            
            return [c.to_dict(include_resumes=True) for c in candidates]
    except Exception as e:
        logger.error(f"Error finding duplicates: {str(e)}")
        return []


def merge_candidates(primary_id: int, duplicate_id: int) -> bool:
    """
    Merge duplicate candidate (future implementation)
    
    Args:
        primary_id: ID of primary candidate to keep
        duplicate_id: ID of duplicate to merge
        
    Returns:
        True if successful, False otherwise
    """
    logger.warning("Candidate merging not yet implemented")
    return False