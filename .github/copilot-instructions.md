# AI Development Platform - Copilot Instructions

## Project Overview

This is a full-stack AI Development Platform with:

- **Backend**: FastAPI (Python 3.11+) with async PostgreSQL, Redis, Qdrant
- **Frontend**: React 18 + TypeScript + Vite + shadcn/ui
- **CLI**: Python Typer CLI with Rich output

## Tech Stack

### Backend

- FastAPI with async/await patterns
- SQLAlchemy 2.0 async ORM with PostgreSQL
- Alembic for database migrations
- Redis for caching and rate limiting
- Qdrant for vector storage (RAG)
- Celery for background tasks
- JWT authentication with python-jose

### Frontend

- React 18 with TypeScript
- Vite for fast builds
- shadcn/ui (Radix UI + Tailwind CSS)
- Zustand for state management
- TanStack Query for data fetching
- Recharts for analytics

### CLI

- Typer for CLI framework
- Rich for beautiful terminal output
- YAML configuration

## Code Conventions

### Python (Backend)

- Use async/await for all I/O operations
- Type hints required for all functions
- Pydantic models for request/response validation
- Follow PEP 8 style guide
- Use `ruff` for linting

### TypeScript (Frontend)

- Strict TypeScript mode enabled
- Use functional components with hooks
- Prefer named exports
- Use absolute imports from `@/`

### API Design

- RESTful endpoints under `/api/v1/`
- JWT Bearer token authentication
- Standard response format with `data`, `message`, `success`

## Directory Structure

```
backend/           # FastAPI backend
├── api/           # API routes and models
├── core/          # Core config, security, database
├── services/      # Business logic
└── workers/       # Celery background tasks

frontend/          # React dashboard
├── src/
│   ├── components/  # UI components
│   ├── pages/       # Page components
│   ├── hooks/       # Custom hooks
│   ├── stores/      # Zustand stores
│   └── services/    # API services

cli/                 # Python CLI tool
```

## Running the Project

```bash
# Start all services
docker-compose up -d

# Backend only
cd backend && uvicorn main:app --reload

# Frontend only
cd frontend && npm run dev

# CLI
cd cli && python -m ai_platform --help
```
