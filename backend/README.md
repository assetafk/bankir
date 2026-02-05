# Banking Service Backend

Production-ready banking service backend built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker, Redis, and Celery.

## Quick Start

### With Docker (Recommended)

From the project root:

```bash
docker-compose up -d
docker-compose exec app alembic upgrade head
```

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run database migrations**:
```bash
alembic upgrade head
```

4. **Start the development server**:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
backend/
├── app/                    # Application code
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── api/               # API routes
│   ├── services/          # Business logic
│   ├── core/              # Core utilities
│   └── tasks/             # Celery tasks
├── alembic/                # Database migrations
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
