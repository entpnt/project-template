from flask import Flask, request, jsonify
import os
import uuid
from datetime import datetime
from functools import wraps
from .models.mongodb import mongo, ApiKey, Project, Document, Conversation
from .utils.response import api_response, APIResponse

app = Flask(__name__)

# Configuration
app.config['MONGO_URI'] = os.getenv(
    'MONGO_URI',
    'mongodb://app_user:app_pass@mongodb:27017/project_db?authSource=admin'
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize MongoDB extension
mongo.init_app(app)

# Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        response = APIResponse()
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return response.error("API key is missing", code=401)
        
        if not ApiKey.validate(api_key):
            return response.error("Invalid API key", code=401)
        
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route('/api/projects', methods=['POST'])
@require_api_key
@api_response
def create_project(response):
    """Create a new project."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return response.error(
            message="Missing required fields",
            code=400
        )

    try:
        name = data['name']
        description = data.get('description', '')
        
        # Create project
        project_id = Project.create(name, description)
        
        return response.success(
            data={"id": project_id},
            meta={
                "name": name
            }
        )
    
    except Exception as e:
        return response.error(str(e), code=400)

@app.route('/api/projects/<project_id>', methods=['GET'])
@require_api_key
@api_response
def get_project(response, project_id):
    """Get project details by ID."""
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return response.error("Project not found", code=404)
            
        return response.success(
            data=project
        )
    
    except Exception as e:
        return response.error(str(e), code=400)

@app.route('/api/projects/<project_id>/documents', methods=['POST'])
@require_api_key
@api_response
def add_document(response, project_id):
    """Add a document to a project."""
    data = request.get_json()
    
    if not data or 'document_type' not in data or 'content' not in data:
        return response.error(
            message="Missing required fields",
            code=400
        )
    
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return response.error("Project not found", code=404)
        
        document_type = data['document_type']
        content = data['content']
        
        document_id = Document.create(
            project_id=project_id,
            document_type=document_type,
            content=content
        )
        
        return response.success(
            data={"document_id": document_id}
        )
    
    except Exception as e:
        return response.error(str(e), code=400)

@app.route('/api/projects/<project_id>/documents', methods=['GET'])
@require_api_key
@api_response
def get_documents(response, project_id):
    """Get all documents for a project."""
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return response.error("Project not found", code=404)
        
        document_type = request.args.get('type')
        documents = Document.get_by_project(project_id, document_type)
        
        return response.success(
            data=documents
        )
    
    except Exception as e:
        return response.error(str(e), code=400)

@app.route('/api/projects/<project_id>/conversations', methods=['POST'])
@require_api_key
@api_response
def add_message(response, project_id):
    """Add a message to project conversations."""
    data = request.get_json()
    
    if not data or 'message' not in data or 'user' not in data:
        return response.error(
            message="Missing required fields",
            code=400
        )
    
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return response.error("Project not found", code=404)
        
        message = data['message']
        user = data['user']
        metadata = data.get('metadata', {})
        
        message_id = Conversation.create(
            project_id=project_id,
            user=user,
            message=message,
            metadata=metadata
        )
        
        return response.success(
            data={"message_id": message_id}
        )
    
    except Exception as e:
        return response.error(str(e), code=400)

@app.route('/api/projects/<project_id>/conversations', methods=['GET'])
@require_api_key
@api_response
def get_conversation_history(response, project_id):
    """Get conversation history for a project."""
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return response.error("Project not found", code=404)
        
        limit = request.args.get('limit', 100, type=int)
        conversation_history = Conversation.get_by_project(project_id, limit)
        
        return response.success(
            data=conversation_history
        )
    
    except Exception as e:
        return response.error(str(e), code=400)

@app.route('/health', methods=['GET'])
@api_response
def health_check(response):
    """Health check endpoint."""
    try:
        # Ping MongoDB
        mongo.cx.admin.command('ping')
        return response.success(
            data={"status": "healthy"},
            meta={"database": "connected"}
        )
    except Exception as e:
        return response.error(
            message="Service unhealthy",
            code=500,
            trace=str(e)
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('APP_PORT', 5000))) 