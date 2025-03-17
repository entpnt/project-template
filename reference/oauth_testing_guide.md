# Project Flow API Testing Guide

This guide explains how to use the Postman collection to test the Project Flow API, which supports both OAuth 2.0 and API Key authentication.

## Prerequisites

1. Ensure Project Flow is running using Docker Compose:
   ```bash
   sudo docker compose up -d
   ```

2. Install [Postman](https://www.postman.com/downloads/)

## Importing the Collection

1. Open Postman
2. Click on "Import" in the top left
3. Select the file `reference/oauth_testing_collection.json`
4. Click "Import" to add the collection to your workspace

## Setting Up Collection Variables

Before running the tests, you may want to configure these key variables:

1. **API Key**: If you're using API key authentication, set the `api_key` variable
2. **User Credentials**: The collection includes default test user credentials, which you can change:
   - `user_username`: Username for test account (default: "testuser")
   - `user_password`: Password for test account (default: "TestPassword123")
   - `user_email`: Email for test account (default: "testuser@example.com")

To update these variables:
1. Click on the collection name "Project Flow API" (top level)
2. Click "Variables" 
3. Update the "CURRENT VALUE" column for any variables you want to change
4. Click "Save"

## Authentication Methods

The Project Flow API supports two authentication methods:

### 1. OAuth 2.0 (Recommended)

OAuth 2.0 is the recommended authentication mechanism for secure applications. The collection includes all necessary requests to test the full OAuth flow.

### 2. Legacy API Key

For backward compatibility, the API also accepts API key authentication. Each request in the collection can be toggled between OAuth and API key authentication by enabling/disabling the corresponding headers.

## Using the Collection

The collection is organized into sections that reflect the API structure:

### 1. System Health

Use these endpoints to verify the API is running correctly:

- **Health Check**: Basic API health check
- **Database Health Check**: Verify MongoDB connection

### 2. OAuth User Management

1. **Register User**: Creates a test user account
   - Uses the user credentials from collection variables (`user_username`, `user_email`, `user_password`)

2. **User Login**: Logs in with the created user
   - Uses the username and password from collection variables
   - This establishes a session for the browser-based OAuth flow

3. **Current User**: Get information about the currently authenticated user
   - This endpoint can be accessed with either OAuth token or API key

### 3. OAuth Client Management

1. **Create OAuth Client**: Creates an OAuth client application
   - This step automatically saves the client_id and client_secret to collection variables
   - Note: You must be logged in (from previous step) to create a client

### 4. OAuth Authorization Flow

1. **Authorization URL (Browser Step)**:
   - This is a browser step. Click "Send" to see the complete URL
   - Copy this URL and open it in your browser
   - Log in if prompted
   - Approve the authorization request
   - After approval, you'll be redirected to the callback URL with a code parameter
   - Copy the `code` value from the URL (e.g., `http://localhost:8000/callback?code=SOME_CODE_HERE`)
   - In Postman, click on the collection name "Project Flow API" (top level)
   - Click "Variables" and paste the code into the "auth_code" variable's "CURRENT VALUE" field
   - Click "Save"

2. **Exchange Code for Token**: Exchanges the authorization code for an access token
   - This step automatically updates the access_token variable for subsequent requests

3. **Refresh Token**: Get a new access token using a refresh token
   - Use this when the access token expires

4. **Token Introspection**: Check token validity and details

5. **Revoke Token**: Revoke the access token when finished

### 5. Projects

Test project management functionality:

- **Get All Projects**: List all projects for the current user
- **Create Project**: Create a new project
- **Get Project**: Retrieve a specific project by ID
- **Update Project**: Modify a project

### 6. Documents

Test document management functionality:

- **Get Project Documents**: List all documents for a project
- **Create Document**: Add a new document to a project
- **Get Document**: Retrieve a specific document
- **Update Document**: Modify a document's content

### 7. Conversations

Test conversation functionality:

- **Get Project Conversations**: Retrieve conversation history
- **Create Conversation Message**: Add a new message to a conversation
  - Uses the username from collection variables

### 8. Admin

Test admin-only functionality:

- **System Statistics**: Get system-wide statistics (requires admin privileges)

## Understanding Response Format

All API responses follow a standardized format:

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

## Switching Authentication Methods

All requests in the collection can use either OAuth or API Key authentication. To switch between them:

1. In each request, you'll see two authentication headers:
   - `Authorization: Bearer {{access_token}}` (OAuth 2.0)
   - `X-API-Key: {{api_key}}` (Legacy API Key)

2. Enable the header for the authentication method you want to use, and disable the other.

## Troubleshooting

- **401 Unauthorized**: Ensure you've completed all previous steps in order and have valid credentials
- **Invalid auth_code**: Authorization codes expire quickly (usually within 10 minutes). If you get an error, repeat the Authorization URL step
- **Network Error**: Make sure Project Flow is running and accessible at http://localhost:5000

## Notes

- All requests use collection variables, so you don't need to manually update URLs or tokens
- Test scripts automatically save relevant values to collection variables
- The standardized response format may vary from older documentation examples
- OAuth and API Key authentication can be used interchangeably for all protected endpoints 