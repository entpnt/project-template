# API Project Template

A comprehensive Flask API template with MongoDB integration and OAuth 2.0 authentication.

## Features

- **RESTful API**: Well-structured Flask API with proper error handling
- **Authentication**: OAuth 2.0 for secure API authentication with legacy API key support
- **Standardized Responses**: Consistent JSON response format across all endpoints
- **Database**: MongoDB integration with document models
- **Docker**: Containerized setup for easy deployment
- **Documentation**: Comprehensive API documentation

## Authentication

This API uses OAuth 2.0 for authentication, with support for:

- Authorization Code Flow
- Client Credentials Flow
- Refresh Token Flow

The following OAuth endpoints are available:

- `/auth/authorize`: Authorization endpoint (for authorization code flow)
- `/auth/token`: Token endpoint
- `/auth/revoke`: Token revocation endpoint
- `/auth/introspect`: Token introspection endpoint

For legacy support, the API also accepts API key authentication via the `X-API-Key` header.

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

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Environment Variables

Copy the example environment file and update the values:

```bash
cp .env.example .env
```

Update the following values in the `.env` file:

- `API_KEY`: Your API key for legacy authentication
- `SECRET_KEY`: Your application secret key
- `MONGO_URI`: MongoDB connection URI
- `MONGO_DBNAME`: MongoDB database name
- `ADMIN_USERS`: Comma-separated list of admin user IDs
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins

### Running with Docker

```bash
docker-compose up -d
```

### Running Locally

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
flask run
```

## API Documentation

The API exposes the following main resources:

- `/api/projects`: Project management
- `/api/documents`: Document management
- `/api/conversations`: Conversation management

For detailed API documentation, see [spec.md](./spec.md).

## OAuth 2.0 Flows

### Authorization Code Flow

1. Redirect the user to `/auth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=YOUR_REDIRECT_URI&scope=profile email`
2. User authenticates and approves the authorization
3. Server redirects to your redirect URI with an authorization code
4. Exchange the code for an access token by making a POST request to `/auth/token`

### Client Credentials Flow

Make a POST request to `/auth/token` with the following parameters:

- `grant_type`: `client_credentials`
- `client_id`: Your client ID
- `client_secret`: Your client secret
- `scope`: Requested scopes

### Using Access Tokens

Include the access token in the `Authorization` header for API requests:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Development

### Project Structure

```
project/
├── app/
│   ├── __init__.py         # Flask application factory
│   ├── models/             # MongoDB document models
│   ├── routes/             # API route blueprints
│   ├── templates/          # OAuth authorization templates
│   └── utils/              # Utility functions and decorators
├── scripts/
│   ├── clean.sh            # Clean up script
│   ├── docker-entrypoint.sh# Docker entrypoint
│   └── mongo-init.js       # MongoDB initialization
├── Dockerfile              # Application container
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies
├── spec.md                 # API specification
└── README.md               # This file
```

### Adding New API Endpoints

1. Add new routes in the appropriate blueprint file in `app/routes/`
2. Update the MongoDB models in `app/models/` if needed
3. Use the standardized response format with `success_response()` or `error_response()` functions
4. Document the new endpoints in `spec.md`

## Recent Updates

- Implemented standardized response format across all endpoints
- Consolidated utility folders (`util` and `utils`) for better organization
- Updated OAuth implementation to be compatible with Authlib 1.2.1
- Added proper timezone-aware datetime handling
- Updated `/health/db` endpoint with standardized response format

## License

This project is licensed under the MIT License - see the LICENSE file for details. 