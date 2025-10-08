"""
Validation utilities
"""

import re
from typing import Any, Dict, List, Optional
from email_validator import validate_email, EmailNotValidError

def validate_email_format(email: str) -> bool:
    """Validate email format"""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    result = {
        "is_valid": True,
        "score": 0,
        "issues": []
    }
    
    if len(password) < 8:
        result["issues"].append("Password must be at least 8 characters long")
        result["is_valid"] = False
    
    if not re.search(r"[A-Z]", password):
        result["issues"].append("Password must contain at least one uppercase letter")
        result["score"] += 1
    
    if not re.search(r"[a-z]", password):
        result["issues"].append("Password must contain at least one lowercase letter")
        result["score"] += 1
    
    if not re.search(r"\d", password):
        result["issues"].append("Password must contain at least one digit")
        result["score"] += 1
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        result["issues"].append("Password must contain at least one special character")
        result["score"] += 1
    
    # Calculate strength based on score
    if result["score"] >= 4:
        result["strength"] = "strong"
    elif result["score"] >= 2:
        result["strength"] = "medium"
    else:
        result["strength"] = "weak"
    
    return result

def validate_username(username: str) -> Dict[str, Any]:
    """Validate username"""
    result = {
        "is_valid": True,
        "issues": []
    }
    
    if len(username) < 3:
        result["issues"].append("Username must be at least 3 characters long")
        result["is_valid"] = False
    
    if len(username) > 20:
        result["issues"].append("Username must be no more than 20 characters long")
        result["is_valid"] = False
    
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        result["issues"].append("Username can only contain letters, numbers, and underscores")
        result["is_valid"] = False
    
    if username.startswith("_"):
        result["issues"].append("Username cannot start with an underscore")
        result["is_valid"] = False
    
    return result

def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))

def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file type based on extension"""
    if not filename:
        return False
    
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    return f".{file_extension}" in allowed_extensions

def validate_file_size(file_size: int, max_size: int) -> bool:
    """Validate file size"""
    return file_size <= max_size

def validate_search_query(query: str) -> Dict[str, Any]:
    """Validate search query"""
    result = {
        "is_valid": True,
        "issues": [],
        "processed_query": query.strip()
    }
    
    if not result["processed_query"]:
        result["issues"].append("Search query cannot be empty")
        result["is_valid"] = False
    
    if len(result["processed_query"]) < 2:
        result["issues"].append("Search query must be at least 2 characters long")
        result["is_valid"] = False
    
    if len(result["processed_query"]) > 500:
        result["issues"].append("Search query must be no more than 500 characters long")
        result["is_valid"] = False
    
    # Check for potentially harmful patterns
    harmful_patterns = [
        r'<script.*?>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*='
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, result["processed_query"], re.IGNORECASE):
            result["issues"].append("Search query contains potentially harmful content")
            result["is_valid"] = False
            break
    
    return result

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    if len(text) > 1000:
        text = text[:1000]
    
    return text.strip()

def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> Dict[str, Any]:
    """Validate pagination parameters"""
    result = {
        "is_valid": True,
        "issues": [],
        "page": max(1, page),
        "page_size": min(max_page_size, max(1, page_size))
    }
    
    if page < 1:
        result["issues"].append("Page number must be at least 1")
        result["is_valid"] = False
    
    if page_size < 1:
        result["issues"].append("Page size must be at least 1")
        result["is_valid"] = False
    
    if page_size > max_page_size:
        result["issues"].append(f"Page size cannot exceed {max_page_size}")
        result["is_valid"] = False
    
    return result
