"""
XSS (Cross-Site Scripting) Protection Utilities
"""
import re
import html
from typing import Any, Optional
import bleach
from bleach.css_sanitizer import CSSSanitizer


# Allowed HTML tags (empty for maximum security - no HTML allowed)
ALLOWED_TAGS = []  # No HTML tags allowed by default

# Allowed HTML attributes (empty for maximum security)
ALLOWED_ATTRIBUTES = {}

# Allowed CSS properties (empty for maximum security)
ALLOWED_CSS = []

# CSS sanitizer
css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS)


def sanitize_input(value: Any) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    Removes all HTML tags and encodes special characters.
    """
    if value is None:
        return ""
    
    # Convert to string
    str_value = str(value)
    
    # Remove null bytes
    str_value = str_value.replace('\x00', '')
    
    # HTML escape special characters
    str_value = html.escape(str_value, quote=True)
    
    # Remove any remaining HTML tags using bleach
    str_value = bleach.clean(
        str_value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True
    )
    
    # Remove JavaScript event handlers and other dangerous patterns
    dangerous_patterns = [
        r'javascript:',
        r'on\w+\s*=',
        r'<script',
        r'</script>',
        r'<iframe',
        r'</iframe>',
        r'<object',
        r'</object>',
        r'<embed',
        r'<link',
        r'<meta',
        r'expression\s*\(',
        r'vbscript:',
        r'data:text/html',
    ]
    
    for pattern in dangerous_patterns:
        str_value = re.sub(pattern, '', str_value, flags=re.IGNORECASE)
    
    return str_value.strip()


def sanitize_email(email: str) -> str:
    """
    Sanitize email address while preserving valid email format.
    """
    if not email:
        return ""
    
    # Basic email validation and sanitization
    email = email.strip().lower()
    
    # Remove any HTML/script tags
    email = sanitize_input(email)
    
    # Validate email format (basic check)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    
    return email


def sanitize_numeric(value: Any) -> Optional[float]:
    """
    Sanitize numeric input to prevent injection attacks.
    """
    if value is None:
        return None
    
    try:
        # Convert to float
        num_value = float(value)
        
        # Check for NaN or Infinity
        if not (float('-inf') < num_value < float('inf')):
            raise ValueError("Invalid numeric value")
        
        return num_value
    except (ValueError, TypeError):
        raise ValueError("Invalid numeric input")


def sanitize_string_field(value: Any, max_length: Optional[int] = None) -> str:
    """
    Sanitize string field with optional length validation.
    """
    sanitized = sanitize_input(value)
    
    if max_length and len(sanitized) > max_length:
        raise ValueError(f"String exceeds maximum length of {max_length}")
    
    return sanitized


def validate_no_xss_patterns(value: str) -> bool:
    """
    Validate that a string doesn't contain XSS attack patterns.
    """
    if not value:
        return True
    
    xss_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<object',
        r'<embed',
        r'expression\s*\(',
        r'vbscript:',
        r'data:text/html',
        r'&#x',
        r'&#0',
    ]
    
    value_lower = value.lower()
    for pattern in xss_patterns:
        if re.search(pattern, value_lower):
            return False
    
    return True


def encode_for_json(value: Any) -> str:
    """
    Encode value for safe JSON output.
    """
    if value is None:
        return ""
    
    str_value = str(value)
    # HTML escape for JSON context
    return html.escape(str_value, quote=True)
