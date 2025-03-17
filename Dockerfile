# Use official Python slim image with non-root user
FROM python:3.11-slim

# Build arguments
ARG FLASK_ENV=development

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies and clean up
RUN apt-get update && apt-get install -y \
    netcat-traditional \
    curl \
    gnupg \
    && curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
       gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
       --dearmor \
    && echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/7.0 main" | \
       tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y \
       mongodb-mongosh \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script
COPY scripts/docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh && \
    chown appuser:appuser /app/docker-entrypoint.sh

# Copy application code
COPY app/ ./app/

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV FLASK_APP=app.main
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV FLASK_ENV=${FLASK_ENV}

# Use the entrypoint script
CMD ["/app/docker-entrypoint.sh"] 