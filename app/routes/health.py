"""
Health check routes for the API.
"""
from flask import Blueprint, current_app, jsonify, g
from app.models.mongodb import get_mongo_client, mongo
from pymongo.errors import ConnectionFailure
from app.utils.response import success_response, error_response
import time

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Ping MongoDB
        mongo.cx.admin.command('ping')
        
        return success_response(
            data={"status": "healthy"},
            meta={"database": "connected"}
        )
    except Exception as e:
        return error_response(
            message="Service unhealthy",
            status_code=500,
            trace=str(e)
        )

@health_bp.route('/response-format-test', methods=['GET'])
def response_format_test():
    """Test endpoint for the new response format."""
    try:
        # Simulate some processing time
        time.sleep(0.1)
        
        # Return a success response in the required format
        return success_response(
            data={
                "message": "This is a test response",
                "formatted": True,
                "timestamp": time.time()
            },
            meta={
                "version": "1.0",
                "environment": "development"
            }
        )
    except Exception as e:
        # Return an error response in the required format
        return error_response(
            message="Test error response",
            status_code=400,
            error_code=1001,
            trace=str(e)
        )

@health_bp.route('/db', methods=['GET'])
def db_health_check():
    """Database health check endpoint."""
    try:
        # Check MongoDB connection
        client = get_mongo_client()
        db_info = client.server_info()
        
        return success_response(
            data={
                "status": "healthy",
                "mongo_version": db_info.get('version', 'unknown')
            },
            meta={
                "message": "Database connection successful"
            }
        )
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        return error_response(
            message=f"Database connection failed",
            status_code=500,
            trace=str(e)
        ) 