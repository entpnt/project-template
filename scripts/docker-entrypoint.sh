#!/bin/bash
set -e

# Function to wait for MongoDB
wait_for_db() {
    echo "Waiting for MongoDB..."
    while ! nc -z mongodb 27017; do
        echo "MongoDB is not ready... waiting"
        sleep 1
    done
    echo "MongoDB is reachable!"
    
    # Additional check: wait for MongoDB to be ready for connections
    echo "Checking if MongoDB is ready for connections..."
    max_attempts=30
    attempts=0
    
    while [ $attempts -lt $max_attempts ]; do
        if mongosh --quiet mongodb:27017/admin --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            echo "MongoDB is ready for connections."
            return 0
        fi
        
        attempts=$((attempts+1))
        echo "MongoDB not yet ready for connections, attempt $attempts/$max_attempts..."
        sleep 2
    done
    
    echo "MongoDB failed to become ready in time."
    return 1
}

# Function to check required environment variables
check_env_vars() {
    required_vars=("API_KEY" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: Required environment variable $var is not set"
            exit 1
        fi
    done
}

# Main execution
echo "Checking environment variables..."
check_env_vars

echo "Starting application initialization..."
wait_for_db

echo "Initializing database..."
cd /app
PYTHONPATH=/app python -c "from app.init_db import init_db; init_db()"

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:5000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    "app:create_app()" 