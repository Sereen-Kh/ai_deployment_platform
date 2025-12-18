# AI Development Platform

A comprehensive full-stack AI Development Platform for deploying, managing, and monitoring AI models with RAG capabilities.

![CI/CD](https://github.com/yourusername/ai-deployment-platform/workflows/CI%2FCD%20Pipeline/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🚀 Features

- **🤖 AI Model Deployments**: Deploy and manage Gemini, GPT-4, Claude, and other LLM models
- **🆓 Free Tier Support**: Uses Google Gemini by default (free API tier available!)
- **📚 RAG Knowledge Base**: Upload documents and query with semantic search
- **📊 Analytics Dashboard**: Real-time usage metrics, cost tracking, and visualizations
- **🔐 Authentication**: Secure JWT-based auth with API key management
- **🎨 Modern UI**: Beautiful React dashboard with shadcn/ui components
- **⚡ CLI Tool**: Powerful command-line interface for automation
- **🐳 Docker Ready**: One-command deployment with Docker Compose

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │     │    Backend      │     │   CLI Tool      │
│   React + Vite  │────▶│    FastAPI      │◀────│   Python/Typer  │
│   TypeScript    │     │    Python       │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │     │     Redis       │     │     Qdrant      │
│    Database     │     │  Cache/Queue    │     │  Vector Store   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🛠️ Tech Stack

### Backend

- **FastAPI** - Modern async Python web framework
- **PostgreSQL 15** - Primary database with SQLAlchemy 2.0 async ORM
- **Redis 7** - Caching, rate limiting, and Celery broker
- **Qdrant** - Vector database for RAG embeddings
- **Celery** - Background task processing
- **Alembic** - Database migrations

### Frontend

- **React 18** - UI library with hooks
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **shadcn/ui** - Beautiful UI components (Radix + Tailwind)
- **Zustand** - Lightweight state management
- **TanStack Query** - Data fetching and caching
- **Recharts** - Analytics visualizations

### CLI

- **Typer** - CLI framework
- **Rich** - Beautiful terminal output
- **HTTPX** - Async HTTP client

## 📦 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-deployment-platform.git
cd ai-deployment-platform
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Gemini API key
```

Required environment variables:

- `GEMINI_API_KEY` - Your Google Gemini API key (FREE at https://ai.google.dev/)
- `SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)

Optional:

- `OPENAI_API_KEY` - Your OpenAI API key (optional)
- `ANTHROPIC_API_KEY` - Your Anthropic API key (optional)

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

This starts:

- Backend API at `http://localhost:8000`
- Frontend at `http://localhost:80`
- PostgreSQL at `localhost:5432`
- Redis at `localhost:6379`
- Qdrant at `localhost:6333`

### 4. Access the Application

- **Dashboard**: http://localhost
- **API Docs**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc

## 🔧 Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### CLI

```bash
cd cli

# Install in development mode
pip install -e .

# Or run directly
python -m ai_platform --help
```

## 📚 CLI Usage

```bash
# Login
ai-platform login

# List deployments
ai-platform deployments list

# Create a deployment
ai-platform deployments create --name "My GPT-4" --model gpt-4

# Start/stop deployments
ai-platform deployments start <deployment-id>
ai-platform deployments stop <deployment-id>

# Invoke a deployment
ai-platform deployments invoke <deployment-id> --prompt "Hello, AI!"

# RAG operations
ai-platform rag collections
ai-platform rag create --name "Knowledge Base"
ai-platform rag upload --collection <id> ./document.pdf
ai-platform rag query --collection <id> --query "What is..."

# Analytics
ai-platform analytics dashboard
ai-platform analytics usage --period 7d
ai-platform analytics costs --period 30d

# Configuration
ai-platform config show
ai-platform config set api_url http://localhost:8000
```

## 🔌 API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token

### Deployments

- `GET /api/v1/deployments` - List deployments
- `POST /api/v1/deployments` - Create deployment
- `GET /api/v1/deployments/{id}` - Get deployment
- `DELETE /api/v1/deployments/{id}` - Delete deployment
- `POST /api/v1/deployments/{id}/start` - Start deployment
- `POST /api/v1/deployments/{id}/stop` - Stop deployment
- `POST /api/v1/deployments/{id}/invoke` - Invoke deployment

### RAG

- `GET /api/v1/rag/collections` - List collections
- `POST /api/v1/rag/collections` - Create collection
- `POST /api/v1/rag/collections/{id}/documents` - Upload document
- `POST /api/v1/rag/collections/{id}/query` - Query collection

### Analytics

- `GET /api/v1/analytics/dashboard` - Dashboard metrics
- `GET /api/v1/analytics/usage` - Usage statistics
- `GET /api/v1/analytics/costs` - Cost breakdown

## 📁 Project Structure

```
ai_deployment_platform/
├── backend/
│   ├── api/
│   │   ├── models/         # Pydantic + SQLAlchemy models
│   │   └── routes/         # API route handlers
│   ├── core/               # Config, security, database
│   ├── services/           # Business logic
│   ├── workers/            # Celery tasks
│   ├── alembic/            # Database migrations
│   ├── main.py             # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   └── ui/         # shadcn/ui components
│   │   ├── pages/          # Page components
│   │   ├── stores/         # Zustand stores
│   │   ├── services/       # API client
│   │   └── hooks/          # Custom hooks
│   ├── package.json
│   └── vite.config.ts
├── cli/
│   ├── ai_platform/        # CLI package
│   └── pyproject.toml
├── docker-compose.yml
├── .github/workflows/      # CI/CD pipelines
└── README.md
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 🚀 Deployment

### Docker Compose (Production)

```bash
# Build and start all services
docker-compose -f docker-compose.yml up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Kubernetes

Kubernetes manifests are available in the `k8s/` directory (coming soon).

## 🔒 Security

- JWT-based authentication with refresh tokens
- Bcrypt password hashing
- Rate limiting per user/IP
- CORS configuration
- API key authentication for programmatic access
- Input validation with Pydantic

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- Create an issue for bug reports or feature requests
- Check the [API documentation](http://localhost:8000/docs) for API details
- Review the [contributing guidelines](CONTRIBUTING.md) before submitting PRs
