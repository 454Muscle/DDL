"""Utility functions"""
import hashlib
import secrets
from typing import Optional
from fastapi import HTTPException


def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def parse_file_size_to_bytes(size_str: str) -> Optional[int]:
    """Convert file size string to bytes for filtering"""
    if not size_str:
        return None
    size_str = size_str.upper().strip()
    try:
        if 'GB' in size_str:
            return int(float(size_str.replace('GB', '').strip()) * 1024 * 1024 * 1024)
        elif 'MB' in size_str:
            return int(float(size_str.replace('MB', '').strip()) * 1024 * 1024)
        elif 'KB' in size_str:
            return int(float(size_str.replace('KB', '').strip()) * 1024)
        elif 'B' in size_str:
            return int(float(size_str.replace('B', '').strip()))
        else:
            return int(float(size_str) * 1024 * 1024)  # Assume MB
    except (ValueError, TypeError):
        return None


def validate_http_url(url: str) -> str:
    """Validate and return HTTP/HTTPS URL"""
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="Site URL is required")
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Site URL must start with http:// or https://")
    return url
