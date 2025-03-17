# Project Template Specification

## Overview
This template provides a foundation for building Flask-based APIs with MongoDB integration. It includes structured document storage, API authentication, and Docker containerization.

## Technology Stack
- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Containerization**: Docker & Docker Compose
- **Authentication**: OAuth 2.0 and API key-based (legacy)

## Core Components

### API Structure
- RESTful API endpoints
- Standardized JSON response format
- OAuth 2.0 authentication with API key fallback
- Error handling and consistent response structure

### Database Structure
The MongoDB database uses the following collections:

1. **api_keys**: Store API keys for legacy authentication
   - key: string (unique)
   - description: string
   - created_at: datetime
   - expires_at: datetime
   - active: boolean

2. **users**: User accounts for OAuth authentication
   - user_id: string (unique)
   - username: string (unique)
   - email: string
   - password: string (hashed)
   - is_active: boolean
   - is_admin: boolean
   - created_at: datetime
   - updated_at: datetime

3. **oauth_clients**: OAuth 2.0 client applications
   - client_id: string (unique)
   - client_secret: string
   - client_name: string
   - client_uri: string
   - redirect_uris: array
   - grant_types: array
   - response_types: array
   - scope: string
   - created_at: datetime
   - updated_at: datetime

4. **oauth_tokens**: OAuth 2.0 access and refresh tokens
   - client_id: string (reference to oauth_clients)
   - user_id: string (reference to users)
   - token_type: string
   - access_token: string
   - refresh_token: string
   - scope: string
   - issued_at: datetime
   - expires_at: datetime

5. **projects**: Main project metadata
   - project_id: string (unique)
   - name: string
   - description: string
   - user_id: string (reference to users)
   - created_at: datetime
   - updated_at: datetime
   - status: string

6. **documents**: Project-related documents with configurable types
   - document_id: string (unique)
   - project_id: string (reference to projects)
   - document_type: string (e.g., "ideation", "business_case", "charter")
   - content: string or object
   - created_at: datetime
   - updated_at: datetime

7. **conversations**: Project-related chat history
   - message_id: string (unique)
   - project_id: string (reference to projects)
   - timestamp: datetime
   - user: string
   - message: string
   - metadata: object (optional)

### API Endpoints

#### Authentication
Endpoints can be authenticated using OAuth 2.0 Bearer tokens or legacy API keys:

OAuth 2.0 (preferred):
```
Authorization: Bearer your-access-token
```

Legacy API Key:
```
X-API-Key: your-api-key
```

#### Project Management
- `POST /api/projects` - Create a new project
- `GET /api/projects/{project_id}` - Get project details
- `PUT /api/projects/{project_id}` - Update project
- `DELETE /api/projects/{project_id}` - Delete project

#### Document Management
- `POST /api/projects/{project_id}/documents` - Add document
- `GET /api/projects/{project_id}/documents` - List documents
- `GET /api/projects/{project_id}/documents/{document_id}` - Get document
- `PUT /api/projects/{project_id}/documents/{document_id}` - Update document
- `DELETE /api/projects/{project_id}/documents/{document_id}` - Delete document

#### Conversation Management
- `POST /api/projects/{project_id}/conversations` - Add message
- `GET /api/projects/{project_id}/conversations` - Get conversation history

### System Health
- `GET /health` - System health check
- `GET /health/db` - Database health check

## Development Guidelines

### Code Organization
- Follow modular structure with clear separation of concerns
- Use consistent naming conventions
- Add docstrings to all functions and classes
- Include type hints where appropriate

### Testing
- Write unit tests for all business logic
- Include integration tests for API endpoints
- Test edge cases and error conditions

### Security
- Validate all input data
- Use environment variables for secrets
- Implement proper error handling
- Apply rate limiting for API endpoints

## Deployment

### Docker Configuration
The Docker setup includes:
- Application container (Flask API)
- MongoDB container
- Volume for persistent data storage
- Network for container communication

### Environment Variables
Required environment variables:
- `SECRET_KEY`: Used for Flask session encryption
- `API_KEY`: Default API key for authentication
- `MONGO_URI`: MongoDB connection URI
- `MONGO_DBNAME`: MongoDB database name

Optional environment variables:
- `FLASK_ENV`: development or production
- `APP_PORT`: Port for the Flask application
- `ADMIN_USERS`: Comma-separated list of admin user IDs
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins

## Extension Points
The template is designed to be extended with:
- Additional document types
- File uploads
- External service integrations
- Advanced search capabilities

# API Specification

This document outlines the API endpoints and their expected behavior.

## Standardized Response Format

All API responses follow a consistent format:

```json
{
  "data": { /* The actual response data */ },
  "meta": { /* Additional metadata */ },
  "duration": "10.45ms", /* Request processing time */
  "error": null /* Error information, null for successful responses */
}
```

For error responses:

```json
{
  "data": {},
  "meta": {},
  "duration": "5.32ms",
  "error": {
    "code": 404,
    "message": "Resource not found",
    "trace": null /* Stack trace, included for 5xx errors in debug mode only */
  }
}
```

## Authentication

The API supports two authentication methods:

### OAuth 2.0 Authentication (Recommended)

OAuth 2.0 is the recommended authentication mechanism for this API. The following OAuth flows are supported:

1. **Authorization Code Flow** - for web applications
2. **Client Credentials Flow** - for server-to-server communication
3. **Refresh Token Flow** - for renewing access tokens

For protected endpoints, include the access token in the Authorization header:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Legacy API Key Authentication

For backward compatibility, the API also supports API key authentication. Include the API key in the header:

```
X-API-Key: YOUR_API_KEY
```

## OAuth 2.0 Endpoints

### Register User

```
POST /auth/register
```

Register a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "data": {
    "user_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "username": "johndoe",
    "email": "john@example.com"
  },
  "duration": "45.67ms",
  "error": null,
  "meta": {}
}
```

### User Login

```
POST /auth/login
```

Log in and obtain a session for web flows.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "data": {
    "user_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "username": "johndoe",
    "email": "john@example.com"
  },
  "duration": "38.21ms",
  "error": null,
  "meta": {}
}
```

### Create OAuth Client

```
POST /auth/client
```

Create a new OAuth client for your application.

**Authorization:** OAuth 2.0 token required

**Request Body:**
```json
{
  "client_name": "My Application",
  "redirect_uris": "https://myapp.example.com/callback http://localhost:3000/callback",
  "client_uri": "https://myapp.example.com"
}
```

**Response:**
```json
{
  "data": {
    "client_id": "abc123def456ghi789jkl",
    "client_secret": "very_long_and_secure_secret_here",
    "client_name": "My Application",
    "redirect_uris": ["https://myapp.example.com/callback", "http://localhost:3000/callback"]
  },
  "duration": "42.89ms",
  "error": null,
  "meta": {}
}
```

### Authorization Endpoint

```
GET /auth/authorize
```

Initiate the authorization code flow. This will display a user consent page.

**Query Parameters:**
- `client_id` - Your OAuth client ID
- `response_type` - Must be "code"
- `redirect_uri` - Must match one of the registered redirect URIs
- `scope` - Space-separated list of requested scopes (e.g., "profile email")
- `state` - (Optional) A value your client can use to maintain state

**Response:**
The user will be redirected to the specified redirect URI with:
- `code` - The authorization code
- `state` - The state value provided in the request (if any)

### Token Endpoint

```
POST /auth/token
```

Exchange an authorization code for an access token.

**Request Body (Authorization Code Flow):**
```
grant_type=authorization_code
code=YOUR_AUTHORIZATION_CODE
redirect_uri=YOUR_REDIRECT_URI
client_id=YOUR_CLIENT_ID
client_secret=YOUR_CLIENT_SECRET
```

**Request Body (Client Credentials Flow):**
```
grant_type=client_credentials
client_id=YOUR_CLIENT_ID
client_secret=YOUR_CLIENT_SECRET
scope=YOUR_REQUESTED_SCOPE
```

**Request Body (Refresh Token Flow):**
```
grant_type=refresh_token
refresh_token=YOUR_REFRESH_TOKEN
client_id=YOUR_CLIENT_ID
client_secret=YOUR_CLIENT_SECRET
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def456ghi789jklabc123...",
  "scope": "profile email"
}
```

### Token Revocation Endpoint

```
POST /auth/revoke
```

Revoke an access or refresh token.

**Request Body:**
```
token=YOUR_TOKEN
token_type_hint=access_token  # or refresh_token
client_id=YOUR_CLIENT_ID
client_secret=YOUR_CLIENT_SECRET
```

### Token Introspection Endpoint

```
POST /auth/introspect
```

Get information about a token.

**Authorization:** Client credentials required

**Request Body:**
```
token=YOUR_TOKEN
```

**Response (Active Token):**
```json
{
  "active": true,
  "client_id": "abc123def456ghi789jkl",
  "token_type": "Bearer",
  "scope": "profile email",
  "exp": 1601234567,
  "iat": 1601230967,
  "sub": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a"
}
```

**Response (Inactive Token):**
```json
{
  "active": false
}
```

### Get Current User

```
GET /auth/me
```

Get information about the currently authenticated user.

**Authorization:** OAuth 2.0 token required

**Response:**
```json
{
  "data": {
    "user_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "username": "johndoe",
    "email": "john@example.com",
    "is_admin": false
  },
  "duration": "12.34ms",
  "error": null,
  "meta": {}
}
```

## API Endpoints

### Projects

#### Get All Projects

```
GET /api/projects
```

Get all projects for the authenticated user.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Response:**
```json
{
  "data": {
    "projects": [
      {
        "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
        "name": "My Project",
        "description": "This is my project",
        "created_at": "2023-10-15T14:30:00Z",
        "updated_at": "2023-10-15T14:30:00Z",
        "status": "active",
        "user_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a"
      }
    ]
  },
  "duration": "18.45ms",
  "error": null,
  "meta": {}
}
```

#### Create Project

```
POST /api/projects
```

Create a new project.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Request Body:**
```json
{
  "name": "My Project",
  "description": "This is my project"
}
```

**Response:**
```json
{
  "data": {
    "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "name": "My Project",
    "description": "This is my project"
  },
  "duration": "32.15ms",
  "error": null,
  "meta": {}
}
```

#### Get Project

```
GET /api/projects/{project_id}
```

Get details of a specific project.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Response:**
```json
{
  "data": {
    "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "name": "My Project",
    "description": "This is my project",
    "created_at": "2023-10-15T14:30:00Z",
    "updated_at": "2023-10-15T14:30:00Z",
    "status": "active",
    "user_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a"
  },
  "duration": "14.78ms",
  "error": null,
  "meta": {}
}
```

#### Update Project

```
PUT /api/projects/{project_id}
```

Update a project.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "Updated project description",
  "status": "archived"
}
```

**Response:**
```json
{
  "data": {
    "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "name": "Updated Project Name",
    "description": "Updated project description",
    "created_at": "2023-10-15T14:30:00Z",
    "updated_at": "2023-10-16T09:45:00Z",
    "status": "archived",
    "user_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a"
  },
  "duration": "28.91ms",
  "error": null,
  "meta": {}
}
```

### Documents

#### Get Project Documents

```
GET /api/projects/{project_id}/documents
```

Get all documents for a project.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Query Parameters:**
- `type` - (Optional) Filter by document type

**Response:**
```json
{
  "data": {
    "documents": [
      {
        "document_id": "6a7b8c9d-0e1f-2a3b-4c5d-6a7b8c9d0e1f",
        "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
        "document_type": "specification",
        "content": "Document content goes here",
        "created_at": "2023-10-15T15:00:00Z",
        "updated_at": "2023-10-15T15:00:00Z"
      }
    ]
  },
  "duration": "15.67ms",
  "error": null,
  "meta": {}
}
```

#### Create Document

```
POST /api/projects/{project_id}/documents
```

Create a new document for a project.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Request Body:**
```json
{
  "document_type": "specification",
  "content": "Document content goes here"
}
```

**Response:**
```json
{
  "data": {
    "document_id": "6a7b8c9d-0e1f-2a3b-4c5d-6a7b8c9d0e1f",
    "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "document_type": "specification"
  },
  "duration": "27.45ms",
  "error": null,
  "meta": {}
}
```

#### Get Document

```
GET /api/documents/{document_id}
```

Get details of a specific document.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Response:**
```json
{
  "data": {
    "document_id": "6a7b8c9d-0e1f-2a3b-4c5d-6a7b8c9d0e1f",
    "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "document_type": "specification",
    "content": "Document content goes here",
    "created_at": "2023-10-15T15:00:00Z",
    "updated_at": "2023-10-15T15:00:00Z"
  },
  "duration": "12.34ms",
  "error": null,
  "meta": {}
}
```

#### Update Document

```
PUT /api/documents/{document_id}
```

Update a document.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Request Body:**
```json
{
  "content": "Updated document content goes here"
}
```

**Response:**
```json
{
  "data": {
    "document_id": "6a7b8c9d-0e1f-2a3b-4c5d-6a7b8c9d0e1f",
    "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
    "document_type": "specification",
    "content": "Updated document content goes here",
    "created_at": "2023-10-15T15:00:00Z",
    "updated_at": "2023-10-16T10:15:00Z"
  },
  "duration": "21.45ms",
  "error": null,
  "meta": {}
}
```

### Conversations

#### Get Project Conversations

```
GET /api/projects/{project_id}/conversations
```

Get conversation history for a project.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Query Parameters:**
- `limit` - (Optional) Maximum number of messages to return (default: 100)

**Response:**
```json
{
  "data": {
    "conversations": [
      {
        "message_id": "7c8d9e0f-1a2b-3c4d-5e6f-7c8d9e0f1a2b",
        "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a",
        "timestamp": "2023-10-15T16:30:00Z",
        "user": "johndoe",
        "message": "This is a message",
        "metadata": {}
      }
    ]
  },
  "duration": "14.34ms",
  "error": null,
  "meta": {}
}
```

#### Create Conversation Message

```
POST /api/projects/{project_id}/conversations
```

Add a new message to a project's conversation.

**Authorization:** OAuth 2.0 token required with 'profile' scope

**Request Body:**
```json
{
  "user": "johndoe",
  "message": "This is a message",
  "metadata": {
    "source": "web",
    "importance": "normal"
  }
}
```

**Response:**
```json
{
  "data": {
    "message_id": "7c8d9e0f-1a2b-3c4d-5e6f-7c8d9e0f1a2b",
    "project_id": "5f8d0b1c-4b9a-4b8e-8c1a-5f8d0b1c4b9a"
  },
  "duration": "18.23ms",
  "error": null,
  "meta": {}
}
```

### Admin Endpoints

#### Get System Statistics

```
GET /api/admin/stats
```

Get system statistics (admin users only).

**Authorization:** OAuth 2.0 token required with 'admin' scope

**Response:**
```json
{
  "data": {
    "total_projects": 25,
    "total_documents": 103,
    "total_conversations": 458
  },
  "duration": "32.56ms",
  "error": null,
  "meta": {}
}
```

## Health Endpoints

#### Basic Health Check

```
GET /health
```

Check if the API is up and running.

**Response:**
```json
{
  "data": {
    "status": "healthy"
  },
  "duration": "1.25ms",
  "error": null,
  "meta": {
    "database": "connected"
  }
}
```

#### Database Health Check

```
GET /health/db
```

Check if the database connection is working.

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "mongo_version": "6.0.20"
  },
  "duration": "3.45ms",
  "error": null,
  "meta": {
    "message": "Database connection successful"
  }
}
```

## Error Responses

All error responses follow the standardized format with the error field populated:

```json
{
  "data": {},
  "meta": {},
  "duration": "5.67ms",
  "error": {
    "code": 404,
    "message": "Resource not found",
    "trace": null
  }
}
```

### Common Error Codes

- 400 Bad Request - Missing or invalid parameters
- 401 Unauthorized - Authentication required or failed
- 403 Forbidden - Insufficient permissions
- 404 Not Found - Resource not found
- 500 Internal Server Error - Unexpected server error 