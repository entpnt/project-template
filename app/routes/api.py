"""
API routes for the project template.
"""
import uuid
from flask import Blueprint, request, jsonify, g, current_app
from app.models.mongodb import Project, Document, Conversation, User
from app.utils.decorators import auth_required, admin_required
from app.utils.response import success_response, error_response

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Projects

@api_bp.route('/projects', methods=['GET'])
@auth_required('profile')
def get_projects():
    """Get all projects for the authenticated user."""
    user_id = g.get('user_id')
    if not user_id:
        return error_response('User not authenticated', 401)
    
    projects = Project.get_by_user(user_id)
    return success_response({
        'projects': projects
    })

@api_bp.route('/projects', methods=['POST'])
@auth_required('profile')
def create_project():
    """Create a new project."""
    data = request.get_json()
    
    # Basic validation
    if not data or not all(k in data for k in ('name', 'description')):
        return error_response('Missing required fields', 400)
    
    # Create project
    user_id = g.get('user_id')
    project_id = Project.create(
        data['name'],
        data['description'],
        user_id=user_id
    )
    
    return success_response({
        'project_id': project_id,
        'name': data['name'],
        'description': data['description']
    }, 201)

@api_bp.route('/projects/<project_id>', methods=['GET'])
@auth_required('profile')
def get_project(project_id):
    """Get a project by ID."""
    project = Project.get_by_id(project_id)
    
    if not project:
        return error_response('Project not found', 404)
    
    # Check project ownership
    user_id = g.get('user_id')
    if user_id and project.get('user_id') and project.get('user_id') != user_id:
        return error_response('Access denied', 403)
    
    return success_response(project)

@api_bp.route('/projects/<project_id>', methods=['PUT'])
@auth_required('profile')
def update_project(project_id):
    """Update a project."""
    data = request.get_json()
    project = Project.get_by_id(project_id)
    
    if not project:
        return error_response('Project not found', 404)
    
    # Check project ownership
    user_id = g.get('user_id')
    if user_id and project.get('user_id') and project.get('user_id') != user_id:
        return error_response('Access denied', 403)
    
    # Update fields
    updates = {}
    if 'name' in data:
        updates['name'] = data['name']
    if 'description' in data:
        updates['description'] = data['description']
    if 'status' in data:
        updates['status'] = data['status']
    
    if updates:
        Project.update(project_id, **updates)
    
    # Get updated project
    updated_project = Project.get_by_id(project_id)
    return success_response(updated_project)

# Documents

@api_bp.route('/projects/<project_id>/documents', methods=['GET'])
@auth_required('profile')
def get_documents(project_id):
    """Get all documents for a project."""
    project = Project.get_by_id(project_id)
    
    if not project:
        return error_response('Project not found', 404)
    
    # Check project ownership
    user_id = g.get('user_id')
    if user_id and project.get('user_id') and project.get('user_id') != user_id:
        return error_response('Access denied', 403)
    
    document_type = request.args.get('type')
    documents = Document.get_by_project(project_id, document_type)
    
    return success_response({
        'documents': documents
    })

@api_bp.route('/projects/<project_id>/documents', methods=['POST'])
@auth_required('profile')
def create_document(project_id):
    """Create a new document."""
    project = Project.get_by_id(project_id)
    
    if not project:
        return error_response('Project not found', 404)
    
    # Check project ownership
    user_id = g.get('user_id')
    if user_id and project.get('user_id') and project.get('user_id') != user_id:
        return error_response('Access denied', 403)
    
    data = request.get_json()
    
    # Basic validation
    if not data or not all(k in data for k in ('document_type', 'content')):
        return error_response('Missing required fields', 400)
    
    # Create document
    document_id = Document.create(
        project_id,
        data['document_type'],
        data['content']
    )
    
    return success_response({
        'document_id': document_id,
        'project_id': project_id,
        'document_type': data['document_type']
    }, 201)

@api_bp.route('/documents/<document_id>', methods=['GET'])
@auth_required('profile')
def get_document(document_id):
    """Get a document by ID."""
    document = Document.get_by_id(document_id)
    
    if not document:
        return error_response('Document not found', 404)
    
    # Check document's project ownership
    project = Project.get_by_id(document['project_id'])
    user_id = g.get('user_id')
    if user_id and project.get('user_id') and project.get('user_id') != user_id:
        return error_response('Access denied', 403)
    
    return success_response(document)

@api_bp.route('/documents/<document_id>', methods=['PUT'])
@auth_required('profile')
def update_document(document_id):
    """Update a document."""
    document = Document.get_by_id(document_id)
    
    if not document:
        return error_response('Document not found', 404)
    
    # Check document's project ownership
    project = Project.get_by_id(document['project_id'])
    user_id = g.get('user_id')
    if user_id and project.get('user_id') and project.get('user_id') != user_id:
        return error_response('Access denied', 403)
    
    data = request.get_json()
    
    # Basic validation
    if not data or 'content' not in data:
        return error_response('Missing content field', 400)
    
    # Update document
    Document.update(document_id, data['content'])
    
    # Get updated document
    updated_document = Document.get_by_id(document_id)
    return success_response(updated_document)

# Conversations

@api_bp.route('/projects/<project_id>/conversations', methods=['GET'])
@auth_required('profile')
def get_conversations(project_id):
    """Get conversation history for a project."""
    project = Project.get_by_id(project_id)
    
    if not project:
        return error_response('Project not found', 404)
    
    # Check project ownership
    user_id = g.get('user_id')
    if user_id and project.get('user_id') and project.get('user_id') != user_id:
        return error_response('Access denied', 403)
    
    limit = request.args.get('limit', 100, type=int)
    conversations = Conversation.get_by_project(project_id, limit)
    
    return success_response({
        'conversations': conversations
    })

@api_bp.route('/projects/<project_id>/conversations', methods=['POST'])
@auth_required('profile')
def create_conversation(project_id):
    """Create a new conversation message."""
    project = Project.get_by_id(project_id)
    
    if not project:
        return error_response('Project not found', 404)
    
    # Check project ownership
    user_id = g.get('user_id')
    if user_id and project.get('user_id') and project.get('user_id') != user_id:
        return error_response('Access denied', 403)
    
    data = request.get_json()
    
    # Basic validation
    if not data or not all(k in data for k in ('user', 'message')):
        return error_response('Missing required fields', 400)
    
    # Create conversation
    message_id = Conversation.create(
        project_id,
        data['user'],
        data['message'],
        data.get('metadata', {})
    )
    
    return success_response({
        'message_id': message_id,
        'project_id': project_id
    }, 201)

# Admin routes

@api_bp.route('/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    """Get system statistics (admin only)."""
    # This is just an example admin endpoint
    stats = {
        'total_projects': 0,
        'total_documents': 0,
        'total_conversations': 0
    }
    
    return success_response(stats) 