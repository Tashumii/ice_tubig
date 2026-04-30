"""
Utility functions for input validation and sanitization.
"""
import re
from typing import Optional


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input by removing potentially dangerous characters.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(value))
    
    # Trim to max length
    sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_numeric(value: str, min_val: float = None, max_val: float = None) -> Optional[float]:
    """
    Validate and convert numeric input.
    
    Args:
        value: Input string to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated numeric value or None if invalid
    """
    try:
        num = float(value)
        
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None
            
        return num
    except (ValueError, TypeError):
        return None


def validate_integer(value: str, min_val: int = None, max_val: int = None) -> Optional[int]:
    """
    Validate and convert integer input.
    
    Args:
        value: Input string to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated integer value or None if invalid
    """
    try:
        num = int(value)
        
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None
            
        return num
    except (ValueError, TypeError):
        return None


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    clean = (username or "").strip()
    
    if not clean:
        return False, "Username is required"
    if len(clean) < 3:
        return False, "Username must be at least 3 characters"
    if len(clean) > 50:
        return False, "Username must be 50 characters or fewer"
    if re.search(r"\s", clean):
        return False, "Username cannot contain spaces"
    if not re.match(r"^[A-Za-z0-9._-]+$", clean):
        return False, "Username can only contain letters, numbers, dot, underscore, and dash"
    
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if len(password) > 128:
        return False, "Password must be 128 characters or fewer"
    if not password.strip():
        return False, "Password cannot be only spaces"
    
    return True, ""


def escape_html(text: str) -> str:
    """
    Escape HTML special characters to prevent XSS.
    
    Args:
        text: Text to escape
        
    Returns:
        HTML-escaped text
    """
    if not text:
        return ""
    
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    }
    
    result = str(text)
    for char, escape in replacements.items():
        result = result.replace(char, escape)
    
    return result
