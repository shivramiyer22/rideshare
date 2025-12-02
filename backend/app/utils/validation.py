"""
Defines functions for validation.
"""
from typing import Any, Optional, Tuple
import re


def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        bool: True if email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone_number(phone: str) -> bool:
    """
    Validate a phone number format.
    
    Args:
        phone: Phone number to validate
    
    Returns:
        bool: True if phone number is valid, False otherwise
    """
    # Basic phone number validation (adjust pattern as needed)
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, None

