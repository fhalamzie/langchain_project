# Online Mietvertrag - Digital Rental Contract Management

## Project Overview

A multi-tenant digital platform for creating, sending, and managing rental contracts with integrated eSignature capabilities. The system supports both internal organizational users and external tenant clients with role-based access control and automated document workflows.

## Architecture Stack

- **Frontend**: Streamlit with streamlit-authenticator
- **Backend**: FastAPI with Pydantic validation
- **Database**: SQLite (production-ready with PostgreSQL migration path)
- **External APIs**: eSignatures.com for document signing
- **Authentication**: Hash-based with role management
- **File Management**: Temporary runtime processing with optional backup storage

## 📖 Documentation

**ALL project documentation is consolidated in the `/docs` folder. No documentation exists outside this folder.**

### Core Documentation
- [Project Requirements](docs/requirements.md) - Functional and technical requirements
- [Software Architecture](docs/software_architecture.md) - System design and component architecture
- [Information Architecture](docs/information_architecture.md) - Data models and business logic
- [Development Guidelines](docs/Development%20Guidelines.md) - Coding standards and best practices

### Technical Specifications
- [User Interface Specification](docs/ui.md) - UI components and user workflows
- [API Specification](docs/api_specification.md) - REST API documentation
- [Testing Strategy](docs/testing.md) - Testing approach and quality assurance

### Operations & Deployment
- [Environment Configuration](docs/environment_configuration.md) - Setup and configuration guide
- [Deployment Guide](docs/deployment.md) - Production deployment procedures

### Project Management
- [Module Documentation](docs/modules.md) - Component structure and file registry
- [Task Management](docs/tasks.md) - Implementation tasks and progress tracking
- [Status Updates](docs/status.md) - Development progress and architectural decisions
- [Documentation Summary](docs/documentation_summary.md) - Quick reference for LLM context

### Database Schema
Database architecture and models are documented in:
- [Software Architecture - Database Section](docs/software_architecture.md#database-architecture)

**Note**: The Development Guidelines specifically state that **no new .md documentation files should be created**. All documentation must be consolidated within the existing files in `/docs`.

## Quick Start

### Prerequisites
- Python 3.10+
- SQLite 3.x
- eSignatures.com API credentials

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd Online-Mietvertrag

# Environment setup
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with your configuration

# Database initialization
python -c "from db.database import create_tables; create_tables()"

# Application start
streamlit run app.py
```

### Development Workflow
```bash
# Test-Driven Development: Run tests FIRST before implementation
pytest tests/ -v

# Code quality checks
pytest --cov=core --cov=api --cov=ui --cov-report=html

# Run tests
pytest tests/

# Pre-commit validation
pre-commit run --all-files

# Type checking
mypy core/ api/ ui/

# Security scanning
bandit -r core/ api/ ui/
```

## Core Features

### User Management
- Multi-tenant architecture with role-based access
- Roles: master_admin, admin, user, internal
- Profile management and password reset functionality
- Secure authentication with bcrypt password hashing

### Contract Management
- Dynamic form validation with Pydantic models
- Multi-signer support (landlord + tenant(s))
- Status tracking through signature workflow
- Template-based PDF generation with ReportLab

### Document Processing
- Integration with eSignatures.com API
- Runtime PDF processing (no permanent storage)
- Configurable filename schemas for internal users
- Optional backup storage with organized directory structure

### System Administration
- Tenant configuration management
- Object/property management for internal users
- Attachment and template management
- Audit logging and status tracking

## Architecture Overview

### System Components
```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                       │
├─────────────────────────────────────────────────────────────┤
│  Authentication  │  Contract Management  │  Administration  │
│     Module       │       Module          │     Module       │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                        │
├─────────────────────────────────────────────────────────────┤
│   User API   │  Contract API  │  Document API  │  Admin API │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Core                     │
├─────────────────────────────────────────────────────────────┤
│ User Service │Contract Service│Document Service│Tenant Service│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      SQLite Database                       │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Tenant Design
- Tenant isolation at data level
- Shared application instance with tenant-specific configurations
- Role-based access control across tenant boundaries

## Development Principles

All development follows strict guidelines as defined in [Development Guidelines](docs/Development%20Guidelines.md):

- **Documentation Consolidation**: ALL documentation in `/docs` folder only - no new .md files anywhere
- **Test-Driven Development**: All features require upfront test case definition
- **Clean Architecture**: Separation of UI, business logic, and data layers  
- **Security by Design**: Multi-tenant isolation and secure authentication
- **Real Data Testing**: Use production-like data for comprehensive testing

## API Endpoints

### Authentication
```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
```

### Contract Management
```
POST   /api/v1/contracts
GET    /api/v1/contracts/{id}
PUT    /api/v1/contracts/{id}
DELETE /api/v1/contracts/{id}
POST   /api/v1/contracts/{id}/sign
GET    /api/v1/contracts/{id}/status
```

### Document Processing
```
POST   /api/v1/documents/generate
GET    /api/v1/documents/{id}/pdf
POST   /api/v1/documents/{id}/send-signature
```

### Administration
```
GET    /api/v1/admin/tenants
POST   /api/v1/admin/tenants
PUT    /api/v1/admin/tenants/{id}
```

For detailed API documentation, see [API Specification](docs/api_specification.md).

## Environment Configuration

### Required Environment Variables
```bash
# Core Application
SECRET_KEY=your-secret-key-here-minimum-32-chars
DATABASE_URL=sqlite:///./app.db
DEBUG=true

# eSignatures.com Integration
ESIGNATURES_API_KEY=your-api-key-here
ESIGNATURES_SANDBOX=true

# File Storage
MV_BACKUP_ROOT_PATH=./storage/contracts
```

See [Environment Configuration](docs/environment_configuration.md) for complete setup guide.

## Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
```bash
# Production environment setup
pip install -r requirements.txt
export APP_ENV=production
export DEBUG=false
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

For comprehensive deployment procedures, see [Deployment Guide](docs/deployment.md).

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=api --cov=ui --cov-report=html

# Run specific test categories
pytest tests/unit/              # Unit tests
pytest tests/integration/       # Integration tests
pytest tests/e2e/              # End-to-end tests
```

### Test Coverage Targets
- **Unit Tests**: 90% line coverage minimum
- **Integration Tests**: 80% feature coverage
- **E2E Tests**: 100% critical path coverage

See [Testing Strategy](docs/testing.md) for detailed testing approach.

## Security Features

### Authentication & Authorization
- bcrypt password hashing (cost factor: 12)
- Session-based authentication with secure cookies
- Role-based access control (RBAC)
- Multi-tenant data isolation

### Data Protection
- Input validation with Pydantic models
- SQL injection prevention through ORM
- XSS protection in UI components
- CSRF protection enabled

### External Service Security
- API key management for eSignatures.com
- Retry logic with rate limiting compliance
- Circuit breaker pattern for API failures

## Contributing

1. Review [Development Guidelines](docs/Development%20Guidelines.md)
2. **ALL documentation must be in `/docs` folder** - never create .md files elsewhere
3. Ensure test coverage for new features
4. Follow the established architecture patterns
5. Update existing documentation files for any changes
6. Run quality checks before submitting

## License

[Specify your license here]

## Support

**For ALL technical documentation and architecture details, refer exclusively to the `/docs` folder.**

- Development questions: [Development Guidelines](docs/Development%20Guidelines.md)
- API usage: [API Specification](docs/api_specification.md)
- Testing approach: [Testing Strategy](docs/testing.md)
- Deployment help: [Deployment Guide](docs/deployment.md)
- Quick LLM context: [Documentation Summary](docs/documentation_summary.md)