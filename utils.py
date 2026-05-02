"""
Utility functions for input validation and sanitization.
"""
import re
from typing import Optional

STATUS_LABELS = {
    "AVAILABLE": "Ready to Sell",
    "NOT_AVAILABLE": "Freezing",
    "SOLD": "Sold",
    "ON_TIME": "On Time",
    "LATE": "Late",
    "COMPLETED": "Completed",
    "LATE_COMPLETED": "Late, Completed",
    "EARLY_OUT": "Left Early",
    "LATE_EARLY_OUT": "Late and Left Early",
    "OFFSITE": "Not On Site",
    "CLOCK_IN": "Marked On Site",
    "LATE_CLOCK_IN": "Late Arrival",
    "CLOCK_OUT": "Timed Out",
    "EARLY_TIME_OUT": "Left Early",
    "SALE_RECORDED": "Sale Recorded",
    "SALE_BLOCKED": "Sale Blocked",
    "ALREADY_ON_SITE": "Already On Site",
    "ALREADY_TIMED_OUT": "Already Timed Out",
    "TIME_OUT_WITHOUT_CLOCK_IN": "Time Out Blocked",
}

EMPTY_LABELS = {"", "N/A", "NONE", "NULL", "UNASSIGNED"}


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


def humanize_status(value) -> str:
    """Turn database/status constants into words people can read quickly."""
    if value is None:
        return "Not recorded"

    raw = getattr(value, "value", value)
    text = str(raw).strip()
    if text.upper() in EMPTY_LABELS:
        return "Not recorded"

    key = text.upper().replace(" ", "_")
    if key in STATUS_LABELS:
        return STATUS_LABELS[key]

    return text.replace("_", " ").title()


def humanize_name(value, fallback: str = "Not assigned") -> str:
    text = str(value or "").strip()
    if text.upper() in EMPTY_LABELS:
        return fallback
    return text


def clean_display_text(value) -> str:
    """Clean technical constants inside longer user-facing messages."""
    text = str(value or "").strip()
    if not text:
        return "No details provided."

    for code in sorted(STATUS_LABELS, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(code)}\b", STATUS_LABELS[code], text)

    text = text.replace("N/A", "Not recorded")
    text = text.replace("Unassigned", "Not assigned")
    return text


def friendly_error(value) -> str:
    """Remove internal exception wrappers from messages shown in dialogs."""
    text = clean_display_text(value)
    prefixes = (
        "Failed to clock in: ",
        "Failed to clock out: ",
        "Failed to sell ice stock: ",
        "Database execution error: ",
        "Database procedure error 'sp_sell_stock': ",
    )
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                changed = True

    return text or "Something went wrong. Please try again."


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
