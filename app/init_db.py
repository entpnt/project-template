import os
from datetime import datetime, timedelta
import logging
import time
from flask import Flask
from .models.mongodb import mongo, ApiKey

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flag file to track if initialization has been done
INIT_FLAG_FILE = '/tmp/db_initialized'

def create_app():
    """Create and configure Flask application instance."""
    app = Flask(__name__)
    app.config['MONGO_URI'] = os.getenv(
        'MONGO_URI',
        'mongodb://app_user:app_pass@mongodb:27017/project_db?authSource=admin'
    )
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    mongo.init_app(app)
    return app

def init_db():
    """Initialize the database with required collections and default data."""
    # Check if we've already initialized in this container
    if os.path.exists(INIT_FLAG_FILE):
        logger.info("Database already initialized in this container. Skipping initialization.")
        return
    
    # Add a small delay to ensure MongoDB is fully ready
    time.sleep(2)
    
    app = create_app()
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                # Try to ping the database to make sure it's ready
                mongo.cx.admin.command('ping')
                
                # Check if the default API key exists
                default_api_key = os.getenv('API_KEY')
                if not default_api_key:
                    logger.error("API_KEY not found in environment variables")
                    raise ValueError("API_KEY environment variable is required")

                # Check if the key already exists
                existing_key = ApiKey.find_one({'key': default_api_key})
                if not existing_key:
                    # Create default API key
                    ApiKey.create(
                        key=default_api_key,
                        description="Default API key from environment variables"
                    )
                    logger.info("Successfully initialized default API key")
                else:
                    logger.info("Default API key already exists")
                
                # Create flag file to indicate initialization has been done
                with open(INIT_FLAG_FILE, 'w') as f:
                    f.write(str(datetime.utcnow()))
                
                logger.info("Database initialization complete")
                return
                
        except Exception as e:
            retry_count += 1
            logger.warning(f"Database initialization attempt {retry_count} failed: {e}")
            if retry_count >= max_retries:
                logger.error(f"Failed to initialize database after {max_retries} attempts")
                raise
            time.sleep(5)  # Wait 5 seconds before retrying

if __name__ == "__main__":
    init_db() 