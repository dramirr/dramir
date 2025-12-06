FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data/uploads /app/data/backups /app/logs && \
    chmod -R 755 /app/data /app/logs

# Make init.sh executable
RUN chmod +x init.sh

# ✅ CRITICAL: Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production
ENV DEBUG=False
ENV PORT=5000
ENV HOST=0.0.0.0

# Secret keys (CHANGE IN PRODUCTION!)
ENV SECRET_KEY=prod-secret-key-talentdar-2024-change-this
ENV JWT_SECRET_KEY=prod-jwt-secret-key-talentdar-2024-change-this

# Database
ENV DATABASE_URL=sqlite:///data/talentdatar.db
ENV DATABASE_ECHO=False

# API Keys
ENV LIARA_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTM0MzgxMDMwZWM5YThmNWNmZTNlYzkiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzY1MDI5OTA0fQ.SavM3T6y7jy2RbplrtPPf2BuH14QSnwtNKvCyOEsLhc
ENV LIARA_BASE_URL=https://ai.liara.ir/api/690866386a22466d32d318e2/v1

# AI Configuration
ENV AI_MODEL=google/gemini-2.0-flash-001
ENV AI_TEMPERATURE=0.1
ENV AI_MAX_TOKENS=4096

# File Storage
ENV UPLOAD_FOLDER=data/uploads
ENV ALLOWED_EXTENSIONS=pdf,docx,doc,jpg,jpeg,png
ENV MAX_CONTENT_LENGTH=16777216

# Session Configuration
ENV SESSION_COOKIE_SECURE=False
ENV SESSION_COOKIE_HTTPONLY=True
ENV SESSION_COOKIE_SAMESITE=Lax

# Logging
ENV LOG_LEVEL=INFO
ENV LOG_FILE=logs/app.log

# Performance
ENV WORKERS=4
ENV TIMEOUT=300

# Expose port 5000
EXPOSE 5000

# Health check on port 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["bash", "init.sh"]