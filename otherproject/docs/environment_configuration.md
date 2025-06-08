# Environment Configuration

## Overview

Configuration management for the Digital Rental Contract Management System across development, staging, and production environments.

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Core Application Settings
```bash
# Application Environment
APP_ENV=development  # development, staging, production
DEBUG=true          # Set to false in production
SECRET_KEY=your-secret-key-here-minimum-32-chars

# Server Configuration
HOST=0.0.0.0
PORT=8501
API_PORT=8000

# Database Configuration
DATABASE_URL=sqlite:///./app.db  # SQLite for development
# DATABASE_URL=postgresql://user:password@localhost/dbname  # PostgreSQL for production

# Security Settings
PASSWORD_HASH_ROUNDS=12
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_EXPIRATION_HOURS=24
SESSION_TIMEOUT_MINUTES=30
```

### eSignatures.com API Configuration
```bash
# eSignatures.com Integration
ESIGNATURES_API_KEY=your-api-key-here
ESIGNATURES_BASE_URL=https://api.esignatures.com/v1
ESIGNATURES_SANDBOX=true  # Set to false in production
ESIGNATURES_TIMEOUT=30
ESIGNATURES_RETRY_ATTEMPTS=3
ESIGNATURES_RETRY_DELAY=2
```

### File Storage Configuration
```bash
# File Storage
MV_BACKUP_ROOT_PATH=/app/storage/contracts
TEMP_FILE_RETENTION_HOURS=24
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_EXTENSIONS=pdf,jpg,jpeg,png,doc,docx
```

### Email Configuration (Future)
```bash
# Email Settings
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-email-password
SMTP_USE_TLS=true
FROM_EMAIL=noreply@yourdomain.com
```

### Logging Configuration
```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json, text
LOG_FILE_PATH=/app/logs/application.log
LOG_MAX_SIZE_MB=100
LOG_BACKUP_COUNT=5
```

### Security Headers
```bash
# Security Configuration
ENABLE_CORS=true
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
ENABLE_CSRF_PROTECTION=true
SECURE_COOKIES=false  # Set to true in production with HTTPS
```

## Environment-Specific Configurations

### Development Environment (.env.development)
```bash
APP_ENV=development
DEBUG=true
DATABASE_URL=sqlite:///./dev.db
ESIGNATURES_SANDBOX=true
LOG_LEVEL=DEBUG
SECURE_COOKIES=false
MV_BACKUP_ROOT_PATH=./storage/dev
```

### Staging Environment (.env.staging)
```bash
APP_ENV=staging
DEBUG=false
DATABASE_URL=postgresql://staging_user:password@staging-db:5432/staging_db
ESIGNATURES_SANDBOX=true
LOG_LEVEL=INFO
SECURE_COOKIES=true
MV_BACKUP_ROOT_PATH=/app/storage/staging
```

### Production Environment (.env.production)
```bash
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql://prod_user:secure_password@prod-db:5432/prod_db
ESIGNATURES_SANDBOX=false
LOG_LEVEL=WARNING
SECURE_COOKIES=true
MV_BACKUP_ROOT_PATH=/app/storage/production
ENABLE_CSRF_PROTECTION=true
```

## Configuration Loading

### Python Configuration Class
```python
# config.py
import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Core Settings
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    host: str = "0.0.0.0"
    port: int = 8501
    api_port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # eSignatures.com
    esignatures_api_key: str
    esignatures_base_url: str = "https://api.esignatures.com/v1"
    esignatures_sandbox: bool = True
    esignatures_timeout: int = 30
    esignatures_retry_attempts: int = 3
    esignatures_retry_delay: int = 2
    
    # File Storage
    mv_backup_root_path: str = "./storage"
    temp_file_retention_hours: int = 24
    max_upload_size_mb: int = 10
    allowed_file_extensions: str = "pdf,jpg,jpeg,png,doc,docx"
    
    # Security
    password_hash_rounds: int = 12
    jwt_secret_key: str
    jwt_expiration_hours: int = 24
    session_timeout_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file_path: Optional[str] = None
    log_max_size_mb: int = 100
    log_backup_count: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

## Docker Environment Configuration

### Docker Compose Development
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
      - "8000:8000"
    environment:
      - APP_ENV=development
      - DATABASE_URL=sqlite:///./app.db
    volumes:
      - ./storage:/app/storage
    env_file:
      - .env.development
```

### Docker Compose Production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    image: your-registry/mietvertrag:latest
    ports:
      - "8501:8501"
    environment:
      - APP_ENV=production
    env_file:
      - .env.production
    depends_on:
      - db
      
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
volumes:
  postgres_data:
```

## Configuration Validation

### Startup Validation
```python
def validate_configuration():
    """Validate critical configuration settings on startup."""
    required_vars = [
        'SECRET_KEY',
        'ESIGNATURES_API_KEY',
        'JWT_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    # Validate secret key length
    if len(os.getenv('SECRET_KEY', '')) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")
```

## Security Best Practices

### Production Security Checklist
- [ ] Set `DEBUG=false`
- [ ] Use strong, unique `SECRET_KEY` (minimum 32 characters)
- [ ] Configure secure database credentials
- [ ] Enable `SECURE_COOKIES=true` with HTTPS
- [ ] Set appropriate `CORS_ORIGINS`
- [ ] Use production eSignatures.com API (`ESIGNATURES_SANDBOX=false`)
- [ ] Configure proper file storage permissions
- [ ] Set up log rotation and monitoring
- [ ] Use environment variable injection, not .env files in production

### Secrets Management
```bash
# Use Docker secrets or cloud provider secret management
docker secret create secret_key /path/to/secret_key.txt
docker secret create esignatures_api_key /path/to/api_key.txt
```

## Monitoring Configuration

### Health Check Endpoint Configuration
```bash
# Health Check Settings
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_DATABASE=true
HEALTH_CHECK_EXTERNAL_SERVICES=true
HEALTH_CHECK_TIMEOUT=10
```

### Metrics Configuration
```bash
# Application Metrics
METRICS_ENABLED=true
METRICS_PORT=9090
METRICS_PATH=/metrics
```
