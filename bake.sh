#!/bin/bash

# Script to build and run the application with Docker Compose Bake

# Default environment
ENV=${1:-dev}

# Set variables based on environment
case "$ENV" in
  "dev" | "development")
    export ENV="dev"
    export FLASK_ENV="development"
    TARGET="api-development"
    ;;
  "prod" | "production")
    export ENV="prod"
    export FLASK_ENV="production"
    TARGET="api-production"
    ;;
  "test" | "testing")
    export ENV="test"
    export FLASK_ENV="testing"
    TARGET="api-testing"
    ;;
  *)
    echo "Unknown environment: $ENV"
    echo "Usage: $0 [dev|prod|test]"
    exit 1
    ;;
esac

echo "Building for environment: $ENV (FLASK_ENV=$FLASK_ENV)"

# Build the image using Docker Bake
docker buildx bake -f docker-bake.hcl $TARGET

# Run the application with Docker Compose
docker compose up -d

echo "Application started in $ENV environment"
echo "To stop the application, run: docker compose down" 