"""
Authentication and permission decorators.
"""
import functools
from flask import request, jsonify, current_app, g
from app.models.mongodb import ApiKey, require_oauth
from app.utils.response import error_response, APIResponse

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

def api_key_required(func):
    """Legacy decorator for requiring API key authentication.
    
    For backward compatibility. Use require_api_key instead for new code.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return error_response('API key is required', status_code=401)
        
        if not ApiKey.validate(api_key):
            return error_response('Invalid API key', status_code=401)
        
        return func(*args, **kwargs)
    
    return wrapper

def auth_required(scopes=None):
    """Decorator for requiring OAuth 2.0 authentication.
    
    Args:
        scopes (str, optional): Space-separated list of required scopes.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Support legacy API key authentication during transition
            api_key = request.headers.get('X-API-Key')
            if api_key and ApiKey.validate(api_key):
                # This allows older clients to still use API keys
                return func(*args, **kwargs)
            
            # OAuth 2.0 authentication
            try:
                # Use the require_oauth decorator from Authlib
                if scopes:
                    token = require_oauth.acquire_token(scopes)
                else:
                    token = require_oauth.acquire_token()
                
                # Store user info in Flask's g for use in the route
                if token and 'user_id' in token:
                    g.user_id = token['user_id']
                
                return func(*args, **kwargs)
            except Exception as e:
                current_app.logger.error(f"OAuth authentication error: {str(e)}")
                return error_response('Authentication required', status_code=401)
        
        return wrapper
    
    # Support @auth_required without parentheses
    if callable(scopes):
        f = scopes
        scopes = None
        return decorator(f)
    
    return decorator

def admin_required(func):
    """Decorator for requiring admin privileges."""
    @functools.wraps(func)
    @auth_required
    def wrapper(*args, **kwargs):
        # Check if user has admin privileges
        # This would typically check the user's roles or permissions
        # For now, we'll just check if the user is in the admin list
        if 'user_id' in g and g.user_id in current_app.config.get('ADMIN_USERS', []):
            return func(*args, **kwargs)
        
        return error_response('Admin privileges required', status_code=403)
    
    return wrapper 