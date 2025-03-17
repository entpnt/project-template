"""
MongoDB models for the project template.
"""
import os
from datetime import datetime, timedelta, UTC
import uuid
import hashlib
import secrets
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from authlib.integrations.flask_oauth2 import (
    AuthorizationServer, ResourceProtector
)
from authlib.oauth2.rfc6749 import grants, ClientMixin
from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.oauth2.rfc6750 import BearerTokenValidator
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant,
    ClientCredentialsGrant,
    RefreshTokenGrant,
)

mongo = PyMongo()
authorization = AuthorizationServer()
require_oauth = ResourceProtector()

def get_mongo_client():
    """Get the MongoDB client."""
    return mongo.cx

def get_mongo_db():
    """Get the MongoDB database."""
    return mongo.db

def hash_password(password):
    """Simple password hashing using SHA-256.
    
    In production, use a proper password hashing library like passlib.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(length=42):
    """Generate a random token for OAuth."""
    return secrets.token_urlsafe(length)

class BaseDocument:
    """Base class for MongoDB documents."""
    
    @classmethod
    def find_one(cls, query):
        """Find one document."""
        collection = cls._get_collection()
        return collection.find_one(query)
    
    @classmethod
    def find(cls, query, **kwargs):
        """Find documents."""
        collection = cls._get_collection()
        return collection.find(query, **kwargs)
    
    @classmethod
    def insert_one(cls, document):
        """Insert one document."""
        collection = cls._get_collection()
        result = collection.insert_one(document)
        return result.inserted_id
    
    @classmethod
    def update_one(cls, query, update, **kwargs):
        """Update one document."""
        collection = cls._get_collection()
        return collection.update_one(query, update, **kwargs)
    
    @classmethod
    def delete_one(cls, query):
        """Delete one document."""
        collection = cls._get_collection()
        return collection.delete_one(query)
    
    @classmethod
    def _get_collection(cls):
        """Get the collection for this model."""
        return getattr(get_mongo_db(), cls.COLLECTION)

class ApiKey(BaseDocument):
    """Legacy API Key model."""
    
    COLLECTION = 'api_keys'
    
    @classmethod
    def create(cls, key, description, expires_at=None):
        """Create a new API key."""
        if expires_at is None:
            # Default to 1 year expiry
            expires_at = datetime.now(UTC).replace(
                year=datetime.now(UTC).year + 1
            )
            
        document = {
            'key': key,
            'description': description,
            'created_at': datetime.now(UTC),
            'expires_at': expires_at,
            'active': True
        }
        
        return cls.insert_one(document)
    
    @classmethod
    def validate(cls, key):
        """Validate an API key."""
        key_document = cls.find_one({
            'key': key,
            'active': True,
            'expires_at': {'$gt': datetime.now(UTC)}
        })
        
        return key_document is not None

class User(BaseDocument):
    """User model for OAuth authentication."""
    
    COLLECTION = 'users'
    
    @classmethod
    def create(cls, username, email, password, is_admin=False):
        """Create a new user."""
        now = datetime.now(UTC)
        
        document = {
            'user_id': str(uuid.uuid4()),
            'username': username,
            'email': email,
            'password': hash_password(password),
            'is_active': True,
            'is_admin': is_admin,
            'created_at': now,
            'updated_at': now
        }
        
        cls.insert_one(document)
        return document['user_id']
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get a user by ID."""
        return cls.find_one({'user_id': user_id})
    
    @classmethod
    def get_by_username(cls, username):
        """Get a user by username."""
        return cls.find_one({'username': username})
    
    @classmethod
    def validate_password(cls, username, password):
        """Validate user password."""
        user = cls.get_by_username(username)
        if not user:
            return None
        
        if user['password'] == hash_password(password):
            return user
        
        return None

class OAuth2Client(BaseDocument, ClientMixin):
    """OAuth2 Client model."""
    
    COLLECTION = 'oauth_clients'
    
    @classmethod
    def create(cls, client_id, client_secret, client_name, client_uri, 
               redirect_uris, grant_types, response_types, scope):
        """Create a new OAuth client."""
        now = datetime.now(UTC)
        
        document = {
            'client_id': client_id,
            'client_secret': client_secret,
            'client_name': client_name,
            'client_uri': client_uri,
            'redirect_uris': redirect_uris,
            'grant_types': grant_types,
            'response_types': response_types,
            'scope': scope,
            'created_at': now,
            'updated_at': now
        }
        
        cls.insert_one(document)
        return client_id
    
    @classmethod
    def get_by_client_id(cls, client_id):
        """Get a client by client ID."""
        return cls.find_one({'client_id': client_id})
    
    def get_client_id(self):
        """Get client ID for OAuth."""
        return self.get('client_id')
    
    def get_default_redirect_uri(self):
        """Get default redirect URI for OAuth."""
        return self.get('redirect_uris')[0]
    
    def get_allowed_scope(self, scope):
        """Get allowed scope for OAuth."""
        if not scope:
            return ''
        allowed = set(self.get('scope').split())
        return ' '.join(allowed.intersection(set(scope.split())))
    
    def check_redirect_uri(self, redirect_uri):
        """Check if redirect URI is valid."""
        return redirect_uri in self.get('redirect_uris')
    
    def check_client_secret(self, client_secret):
        """Check if client secret is valid."""
        return self.get('client_secret') == client_secret
    
    def check_grant_type(self, grant_type):
        """Check if grant type is allowed."""
        return grant_type in self.get('grant_types')
    
    def check_response_type(self, response_type):
        """Check if response type is allowed."""
        return response_type in self.get('response_types')

class OAuth2Token(BaseDocument):
    """OAuth2 Token model."""
    
    COLLECTION = 'oauth_tokens'
    
    @classmethod
    def create(cls, client_id, token_type, access_token,
               refresh_token=None, scope=None, 
               issued_at=None, expires_in=3600, user_id=None):
        """Create a new OAuth token."""
        if issued_at is None:
            issued_at = datetime.now(UTC)
        
        expires_at = issued_at + timedelta(seconds=expires_in)
        
        document = {
            'client_id': client_id,
            'token_type': token_type,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'scope': scope,
            'issued_at': issued_at,
            'expires_at': expires_at
        }
        
        if user_id:
            document['user_id'] = user_id
        
        cls.insert_one(document)
        return access_token
    
    @classmethod
    def get_by_access_token(cls, access_token):
        """Get a token by access token."""
        return cls.find_one({'access_token': access_token})
    
    @classmethod
    def get_by_refresh_token(cls, refresh_token):
        """Get a token by refresh token."""
        return cls.find_one({'refresh_token': refresh_token})
    
    @classmethod
    def revoke(cls, access_token):
        """Revoke a token."""
        token = cls.get_by_access_token(access_token)
        if token:
            cls.delete_one({'access_token': access_token})
            return True
        return False
    
    @classmethod
    def is_valid(cls, access_token):
        """Check if token is valid."""
        token = cls.get_by_access_token(access_token)
        if not token:
            return False
        
        return token['expires_at'] > datetime.now(UTC)

class Project(BaseDocument):
    """Project model."""
    
    COLLECTION = 'projects'
    
    @classmethod
    def create(cls, name, description, user_id=None):
        """Create a new project."""
        project_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        
        document = {
            'project_id': project_id,
            'name': name,
            'description': description,
            'created_at': now,
            'updated_at': now,
            'status': 'active'
        }
        
        if user_id:
            document['user_id'] = user_id
        
        cls.insert_one(document)
        return project_id
    
    @classmethod
    def get_by_id(cls, project_id):
        """Get a project by ID."""
        return cls.find_one({'project_id': project_id})
    
    @classmethod
    def get_by_user(cls, user_id):
        """Get projects by user ID."""
        return list(cls.find({'user_id': user_id}))
    
    @classmethod
    def update(cls, project_id, **kwargs):
        """Update a project."""
        kwargs['updated_at'] = datetime.now(UTC)
        
        return cls.update_one(
            {'project_id': project_id},
            {'$set': kwargs}
        )

class Document(BaseDocument):
    """Document model for project artifacts."""
    
    COLLECTION = 'documents'
    
    @classmethod
    def create(cls, project_id, document_type, content):
        """Create a new document."""
        now = datetime.now(UTC)
        
        document = {
            'document_id': str(uuid.uuid4()),
            'project_id': project_id,
            'document_type': document_type,
            'content': content,
            'created_at': now,
            'updated_at': now
        }
        
        cls.insert_one(document)
        return document['document_id']
    
    @classmethod
    def get_by_id(cls, document_id):
        """Get a document by ID."""
        return cls.find_one({'document_id': document_id})
    
    @classmethod
    def get_by_project(cls, project_id, document_type=None):
        """Get documents for a project, optionally filtered by type."""
        query = {'project_id': project_id}
        if document_type:
            query['document_type'] = document_type
            
        return list(cls.find(query))
    
    @classmethod
    def update(cls, document_id, content):
        """Update a document."""
        return cls.update_one(
            {'document_id': document_id},
            {
                '$set': {
                    'content': content,
                    'updated_at': datetime.now(UTC)
                }
            }
        )

class Conversation(BaseDocument):
    """Conversation model for project related messages."""
    
    COLLECTION = 'conversations'
    
    @classmethod
    def create(cls, project_id, user, message, metadata=None):
        """Create a new conversation message."""
        if metadata is None:
            metadata = {}
            
        document = {
            'message_id': str(uuid.uuid4()),
            'project_id': project_id,
            'timestamp': datetime.now(UTC),
            'user': user,
            'message': message,
            'metadata': metadata
        }
        
        cls.insert_one(document)
        return document['message_id']
    
    @classmethod
    def get_by_project(cls, project_id, limit=100):
        """Get conversation history for a project."""
        return list(cls.find(
            {'project_id': project_id},
            sort=[('timestamp', 1)],
            limit=limit
        ))

# Global OAuth objects
require_oauth = ResourceProtector()

def get_client(client_id):
    """Retrieve client by client_id"""
    client = OAuth2Client.get_by_client_id(client_id)
    if client:
        return client
    return None

def save_token(token, request):
    """Save token data after request is processed"""
    if request.user:
        user_id = request.user.get('user_id')
    else:
        user_id = None
        
    client = request.client
    
    # Delete previous tokens
    get_mongo_db().oauth_tokens.delete_many({
        'client_id': client.get_client_id(),
        'user_id': user_id
    })
    
    # Create new token
    expires_in = token.pop('expires_in')
    token_data = {
        'client_id': client.get_client_id(),
        'user_id': user_id,
        'token_type': token['token_type'],
        'access_token': token['access_token'],
        'refresh_token': token.get('refresh_token'),
        'scope': token.get('scope'),
        'issued_at': datetime.now(UTC),
        'expires_at': datetime.now(UTC) + timedelta(seconds=expires_in)
    }
    
    get_mongo_db().oauth_tokens.insert_one(token_data)
    return token_data

# Initialize authorization server with the required callbacks
authorization = AuthorizationServer(
    query_client=get_client,
    save_token=save_token
)

# OAuth 2.0 Grant Types Implementation
class AuthCodeGrant(AuthorizationCodeGrant):
    """Authorization Code Grant for OAuth 2.0."""
    
    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_basic', 'client_secret_post']
    
    def save_authorization_code(self, code, request):
        """Save the authorization code."""
        client = request.client
        auth_code = {
            'code': code,
            'client_id': client.get_client_id(),
            'redirect_uri': request.redirect_uri,
            'scope': request.scope,
            'user_id': request.user.get('user_id'),
            'created_at': datetime.now(UTC),
            'expires_at': datetime.now(UTC) + timedelta(minutes=10)
        }
        get_mongo_db().auth_codes.insert_one(auth_code)
        return auth_code
    
    def query_authorization_code(self, code, client):
        """Query the authorization code."""
        auth_code = get_mongo_db().auth_codes.find_one({'code': code})
        if auth_code and auth_code['client_id'] == client.get_client_id():
            return auth_code
        return None
    
    def delete_authorization_code(self, authorization_code):
        """Delete the authorization code."""
        get_mongo_db().auth_codes.delete_one({'code': authorization_code['code']})
    
    def authenticate_user(self, authorization_code):
        """Authenticate the user."""
        user_id = authorization_code['user_id']
        return User.get_by_id(user_id)

class RefreshGrant(RefreshTokenGrant):
    """Refresh Token Grant for OAuth 2.0."""
    
    def authenticate_refresh_token(self, refresh_token):
        """Authenticate the refresh token."""
        token = OAuth2Token.get_by_refresh_token(refresh_token)
        if token and token['expires_at'] > datetime.now(UTC):
            return token
        return None
    
    def authenticate_user(self, credential):
        """Authenticate the user."""
        user_id = credential.get('user_id')
        if user_id:
            return User.get_by_id(user_id)
        return None
    
    def revoke_old_credential(self, credential):
        """Revoke the old credential."""
        OAuth2Token.delete_one({'refresh_token': credential['refresh_token']})

# Setup OAuth 2.0 server
def config_oauth(app):
    """Configure the application to support OAuth 2.0"""
    # Initialize the authorization server with the Flask app
    authorization.init_app(app)
    
    # Register grant types
    authorization.register_grant(AuthCodeGrant, [CodeChallenge(required=True)])
    authorization.register_grant(ClientCredentialsGrant)
    authorization.register_grant(RefreshGrant)
    
    # Define resource token getter function
    def get_token_resource(access_token):
        """Retrieve token for resource access"""
        token = OAuth2Token.get_by_access_token(access_token)
        if token and token['expires_at'] > datetime.now(UTC):
            return token
        return None
    
    # Configure resource protector with a validator
    require_oauth.register_token_validator(DatabaseBearerTokenValidator())
    # Set token getter directly as an attribute instead of using register_token_getter
    DatabaseBearerTokenValidator.authenticate_token = get_token_resource

class DatabaseBearerTokenValidator(BearerTokenValidator):
    def authenticate_token(self, token_string):
        """Authenticate a token string.
        
        Args:
            token_string (str): The token string to authenticate.
            
        Returns:
            The token object if valid, None otherwise.
        """
        # This method will be replaced by the function in config_oauth
        # but we still need to provide an implementation
        token = OAuth2Token.get_by_access_token(token_string)
        if token and token['expires_at'] > datetime.now(UTC):
            return token
        return None

    def request_invalid(self, request):
        """Check if the request is invalid.
        
        Args:
            request: The request object.
            
        Returns:
            bool: True if the request is invalid, False otherwise.
        """
        return False

    def token_revoked(self, token):
        """Check if the token is revoked.
        
        Args:
            token: The token object.
            
        Returns:
            bool: True if the token is revoked, False otherwise.
        """
        return token['expires_at'] < datetime.now(UTC) if token else True 