"""
Authentication utilities for API security.
"""
import functools
from flask import request, jsonify
from ..models.mongodb import ApiKey
from .response import APIResponse

def require_api_key(f):
    """Decorator to require a valid API key for route access."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        response = APIResponse()
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return response.error("API key is missing", code=401)
        
        if not ApiKey.validate(api_key):
            return response.error("Invalid API key", code=401)
        
        return f(*args, **kwargs)
    return decorated 