"""
Authentication routes for the API.
"""
from datetime import datetime
from flask import Blueprint, request, session, url_for, redirect, render_template, jsonify, g
from werkzeug.security import gen_salt
from app.models.mongodb import (
    User, OAuth2Client, OAuth2Token, 
    authorization, generate_token
)
from app.utils.decorators import auth_required
from app.utils.response import success_response, error_response
from authlib.integrations.flask_oauth2 import current_token
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# OAuth 2.0 endpoints

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    # Basic validation
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return error_response('Missing required fields', 400)
    
    # Check if user already exists
    existing_user = User.get_by_username(data['username'])
    if existing_user:
        return error_response('Username already exists', 409)
    
    # Create new user
    user_id = User.create(
        data['username'],
        data['email'],
        data['password'],
        is_admin=data.get('is_admin', False)
    )
    
    return success_response({
        'user_id': user_id,
        'username': data['username'],
        'email': data['email']
    }, 201)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint for user sessions."""
    data = request.get_json()
    
    # Basic validation
    if not data or not all(k in data for k in ('username', 'password')):
        return error_response('Missing required fields', 400)
    
    # Validate credentials
    user = User.validate_password(data['username'], data['password'])
    if not user:
        return error_response('Invalid credentials', 401)
    
    # Set session data
    session['user_id'] = user['user_id']
    session['username'] = user['username']
    
    return success_response({
        'user_id': user['user_id'],
        'username': user['username'],
        'email': user['email']
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint for user sessions."""
    # Clear session
    session.clear()
    return success_response({
        'message': 'Successfully logged out'
    })

@auth_bp.route('/token', methods=['POST'])
def issue_token():
    """Legacy token issuance endpoint using API keys."""
    # This endpoint is kept for backward compatibility
    return error_response('Use OAuth 2.0 for token issuance', 400)

@auth_bp.route('/me', methods=['GET'])
@auth_required
def current_user():
    """Get current authenticated user information."""
    if 'user_id' not in g:
        return error_response('User not authenticated', 401)
    
    user = User.get_by_id(g.user_id)
    if not user:
        return error_response('User not found', 404)
    
    return success_response({
        'user_id': user['user_id'],
        'username': user['username'],
        'email': user['email'],
        'is_admin': user.get('is_admin', False)
    })

# OAuth 2.0 Client Management

@auth_bp.route('/client', methods=['POST'])
@auth_required
def create_client():
    """Create a new OAuth 2.0 client."""
    data = request.get_json()
    user_id = g.get('user_id')
    
    if not user_id:
        return error_response('Authentication required', 401)
    
    # Basic validation
    if not data or not all(k in data for k in ('client_name', 'redirect_uris')):
        return error_response('Missing required fields', 400)
    
    # Generate client credentials
    client_id = gen_salt(24)
    client_secret = gen_salt(48)
    
    # Create the client
    client_id = OAuth2Client.create(
        client_id=client_id,
        client_secret=client_secret,
        client_name=data['client_name'],
        client_uri=data.get('client_uri', ''),
        redirect_uris=data['redirect_uris'].split(),
        grant_types=['authorization_code', 'refresh_token'],
        response_types=['code'],
        scope='profile email',
    )
    
    return success_response({
        'client_id': client_id,
        'client_secret': client_secret,
        'client_name': data['client_name'],
        'redirect_uris': data['redirect_uris'].split()
    }, 201)

# OAuth 2.0 Authorization Server Endpoints

@auth_bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """OAuth 2.0 authorization endpoint."""
    # Login is required
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.get_by_id(session['user_id'])
    if not user:
        return error_response('User not found', 404)
    
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
            return render_template(
                'authorize.html',
                user=user,
                grant=grant
            )
        except Exception as e:
            return error_response(str(e), 400)
    
    # Form submission
    if 'confirm' in request.form:
        grant_user = user
    else:
        grant_user = None
    
    return authorization.create_authorization_response(grant_user=grant_user)

@auth_bp.route('/token', methods=['POST'])
def issue_oauth_token():
    """OAuth 2.0 token endpoint."""
    return authorization.create_token_response()

@auth_bp.route('/revoke', methods=['POST'])
def revoke_token():
    """OAuth 2.0 token revocation endpoint."""
    return authorization.create_endpoint_response('revocation')

@auth_bp.route('/introspect', methods=['POST'])
def introspect_token():
    """OAuth 2.0 token introspection endpoint."""
    # Only authenticated clients can introspect tokens
    auth = request.authorization
    if not auth:
        return error_response('Client authentication required', 401)
    
    client = OAuth2Client.get_by_client_id(auth.username)
    if not client or not client.check_client_secret(auth.password):
        return error_response('Invalid client credentials', 401)
    
    token = request.form.get('token')
    if not token:
        return error_response('Token is required', 400)
    
    token_data = OAuth2Token.get_by_access_token(token)
    if not token_data:
        return jsonify({'active': False})
    
    # Check if token is expired
    if token_data['expires_at'] < datetime.utcnow():
        return jsonify({'active': False})
    
    response = {
        'active': True,
        'client_id': token_data['client_id'],
        'token_type': token_data['token_type'],
        'scope': token_data.get('scope', ''),
        'exp': int(token_data['expires_at'].timestamp()),
        'iat': int(token_data['issued_at'].timestamp())
    }
    
    if 'user_id' in token_data:
        response['sub'] = token_data['user_id']
    
    return jsonify(response) 