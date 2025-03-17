"""
Response utilities for standardized API responses.
"""
import functools
import time
from datetime import datetime
from flask import jsonify, request, g

# Helper function to track request duration
def start_timer():
    """Initialize request timer in Flask g object."""
    g.start_time = time.time()

class APIResponse:
    """Utility class for standardized API responses."""

    def __init__(self):
        self.start_time = time.time()

    def success(self, data=None, meta=None, code=200):
        """Return a success response in the standardized format.
        
        Args:
            data: The data to include in the response (default: {}).
            meta: Additional metadata to include (default: {}).
            code: HTTP status code (default: 200).
            
        Returns:
            A JSON response with the standard format.
        """
        duration = f"{(time.time() - self.start_time) * 1000:.2f}ms"
        
        response = {
            "data": data or {},
            "meta": meta or {},
            "duration": duration,
            "error": None
        }
            
        return jsonify(response), code
    
    def error(self, message="An error occurred", details=None, code=400, trace=None):
        """Return an error response in the standardized format.
        
        Args:
            message: The error message.
            details: Additional error details.
            code: HTTP status code (default: 400).
            trace: Stack trace for debugging (included for 5xx errors).
            
        Returns:
            A JSON response with the standard format.
        """
        duration = f"{(time.time() - self.start_time) * 1000:.2f}ms"
        
        error_obj = {
            "code": code,
            "message": message,
            "trace": trace if trace and code >= 500 else None
        }
        
        if details:
            error_obj["details"] = details
        
        response = {
            "data": {},
            "meta": {},
            "duration": duration,
            "error": error_obj
        }
            
        return jsonify(response), code

def api_response(f):
    """Decorator for API routes to inject an APIResponse instance."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(APIResponse(), *args, **kwargs)
    return wrapper

def success_response(data, meta=None, status_code=200):
    """
    Build a standard success response.
    
    Args:
        data: The data to include in the response.
        meta: Additional metadata to include in the response.
        status_code: The HTTP status code for the response.
        
    Returns:
        A JSON response with a standard format.
    """
    # Calculate request duration
    start_time = getattr(g, 'start_time', time.time())
    duration = f"{(time.time() - start_time) * 1000:.2f}ms"
    
    response = {
        'data': data,
        'meta': meta or {},
        'duration': duration,
        'error': None
    }
    
    return jsonify(response), status_code

def error_response(message, status_code=400, error_code=None, trace=None):
    """
    Build a standard error response.
    
    Args:
        message: The error message.
        status_code: The HTTP status code for the response.
        error_code: An optional application-specific error code.
        trace: Stack trace or additional error information.
        
    Returns:
        A JSON response with a standard format.
    """
    # Calculate request duration
    start_time = getattr(g, 'start_time', time.time())
    duration = f"{(time.time() - start_time) * 1000:.2f}ms"
    
    # Use status_code as error_code if not provided
    if error_code is None:
        error_code = status_code
    
    response = {
        'data': {},
        'meta': {},
        'duration': duration,
        'error': {
            'code': error_code,
            'message': message,
            'trace': trace if trace and status_code >= 500 else None
        }
    }
    
    return jsonify(response), status_code 