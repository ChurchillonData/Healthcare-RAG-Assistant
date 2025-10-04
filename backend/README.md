# Healthcare AI Backend

A comprehensive FastAPI-based backend for a Healthcare AI application with RAG (Retrieval-Augmented Generation) capabilities.

## Features

- **Authentication & Authorization**: JWT-based user authentication with role-based access control
- **Chat System**: AI-powered conversational interface with conversation management
- **Search & RAG**: Semantic search with document retrieval and AI response generation
- **Citation Management**: Source tracking and citation verification
- **Analytics**: User behavior tracking and system metrics
- **Caching**: Redis-based caching for improved performance
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Testing**: Comprehensive test suite with pytest
- **Documentation**: Auto-generated API documentation with FastAPI

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL (with SQLite for development)
- **ORM**: SQLAlchemy 2.0+
- **Authentication**: JWT with python-jose
- **AI**: OpenAI API integration
- **Caching**: Redis
- **Testing**: pytest with async support
- **Migrations**: Alembic

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Application configuration
│   ├── database.py            # Database configuration
│   ├── api/                   # API routes
│   │   ├── deps.py           # API dependencies
│   │   └── v1/
│   │       ├── router.py     # API router configuration
│   │       └── endpoints/    # Individual endpoint modules
│   ├── core/                 # Core utilities
│   │   ├── security.py       # Security utilities
│   │   ├── config.py         # Core configuration
│   │   └── logging.py        # Logging configuration
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic services
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── alembic/                  # Database migrations
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── Dockerfile               # Container configuration
├── pytest.ini              # Test configuration
└── README.md               # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (or SQLite for development)
- Redis (optional, for caching)
- OpenAI API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # For development:
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**:
   ```bash
   # Create database tables
   alembic upgrade head
   ```

6. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## Configuration

### Environment Variables

Key configuration options in `.env`:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key (change in production)
- `OPENAI_API_KEY`: OpenAI API key for AI functionality
- `REDIS_URL`: Redis connection string (optional)
- `ALLOWED_ORIGINS`: CORS allowed origins

### Database Setup

1. **PostgreSQL** (Production):
   ```bash
   createdb healthcare_ai
   export DATABASE_URL="postgresql://user:password@localhost/healthcare_ai"
   ```

2. **SQLite** (Development):
   ```bash
   export DATABASE_URL="sqlite:///./healthcare_ai.db"
   ```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - User logout

### Chat
- `POST /api/v1/chat/conversations` - Create conversation
- `GET /api/v1/chat/conversations` - Get user conversations
- `POST /api/v1/chat/chat` - Send message to AI
- `GET /api/v1/chat/conversations/{id}` - Get conversation
- `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

### Search
- `POST /api/v1/search/documents` - Search documents
- `GET /api/v1/search/suggestions` - Get search suggestions
- `GET /api/v1/search/filters` - Get available filters
- `GET /api/v1/search/trending` - Get trending searches

### Citations
- `GET /api/v1/citations/{id}` - Get citation details
- `POST /api/v1/citations/` - Create citation
- `GET /api/v1/citations/verify/{id}` - Verify citation

### Health
- `GET /health` - Health check
- `GET /health/detailed` - Detailed health check

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api/test_auth.py

# Run with verbose output
pytest -v
```

## Database Migrations

Create and apply migrations:

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Development

### Code Quality

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Lint code
flake8 app tests

# Type checking
mypy app
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Docker

Build and run with Docker:

```bash
# Build image
docker build -t healthcare-ai-backend .

# Run container
docker run -p 8000:8000 healthcare-ai-backend
```

## Deployment

### Environment Setup

1. Set production environment variables
2. Configure database and Redis connections
3. Set up reverse proxy (nginx)
4. Configure SSL certificates
5. Set up monitoring and logging

### Security Considerations

- Change default secret keys
- Use environment variables for sensitive data
- Enable CORS properly
- Set up rate limiting
- Use HTTPS in production
- Regular security updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please create an issue in the repository or contact the development team.
