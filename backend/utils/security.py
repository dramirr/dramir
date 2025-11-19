"""
Security Utilities
"""
from cryptography.fernet import Fernet
import os
import secrets
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ENCRYPTION_KEY_FILE = Path('data/.secret.key')


def _get_or_create_encryption_key() -> bytes:
    """Get or create encryption key"""
    if ENCRYPTION_KEY_FILE.exists():
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            return f.read()
    else:
        ENCRYPTION_KEY_FILE.parent.mkdir(exist_ok=True)
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_FILE, 'wb') as f:
            f.write(key)
        os.chmod(ENCRYPTION_KEY_FILE, 0o600)
        logger.info("Encryption key generated and saved")
        return key


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt API key
    
    Args:
        api_key: Plain text API key
        
    Returns:
        Encrypted API key as string
    """
    try:
        key = _get_or_create_encryption_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(api_key.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        raise


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt API key
    
    Args:
        encrypted_key: Encrypted API key
        
    Returns:
        Decrypted API key
    """
    try:
        key = _get_or_create_encryption_key()
        cipher = Fernet(key)
        decrypted = cipher.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        raise


def generate_secret_key(length: int = 32) -> str:
    """
    Generate random secret key
    
    Args:
        length: Length of secret key
        
    Returns:
        Random secret key
    """
    return secrets.token_hex(length)