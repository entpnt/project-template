"""
Flask application initialization.
"""
import os
import time
import logging
from flask import Flask, g, request, jsonify
from flask.logging import default_handler
from flask_cors import CORS
from app.models.mongodb import mongo, config_oauth
from app.routes.health import health_bp
from app.routes.api import api_bp
from app.routes.auth import auth_bp
from app.utils.response import start_timer, error_response

def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    
    # Load default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_change_in_production'),
        MONGO_URI=os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/app'),
        MONGO_DBNAME=os.environ.get('MONGO_DBNAME', 'app'),
        LOG_LEVEL=os.environ.get('LOG_LEVEL', 'INFO'),
        ADMIN_USERS=os.environ.get('ADMIN_USERS', '').split(','),
        CORS_ORIGINS=os.environ.get('CORS_ORIGINS', '*'),
    )
    
    # Override with any provided configuration
    if config:
        app.config.from_mapping(config)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable CORS
    CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})
    
    # Initialize extensions
    mongo.init_app(app)
    
    # Configure OAuth 2.0
    config_oauth(app)

    # Add request timing middleware
    @app.before_request
    def before_request():
        # Start timer for request duration
        g.start_time = time.time()
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return error_response(
            message='Resource not found',
            status_code=404,
            error_code=404
        )
    
    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception('Unhandled exception')
        return error_response(
            message='Internal server error',
            status_code=500,
            error_code=500,
            trace=str(e) if app.debug else None
        )
    
    return app 