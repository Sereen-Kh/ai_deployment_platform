# Contributing to AI Development Platform

Thank you for your interest in contributing! This document provides guidelines and steps for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python/Node version, etc.)

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue with the `enhancement` label
3. Describe the feature and its use case

### Pull Requests

1. Fork the repository
2. Create a feature branch from `develop`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following our coding standards
4. Write tests for new functionality
5. Ensure all tests pass:

   ```bash
   # Backend
   cd backend && pytest

   # Frontend
   cd frontend && npm test
   ```

6. Commit with clear messages:
   ```bash
   git commit -m "feat: add new feature description"
   ```
7. Push and create a Pull Request to `develop`

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### Local Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ai-deployment-platform.git
cd ai-deployment-platform

# Start infrastructure with Docker
docker-compose up -d postgres redis qdrant

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov ruff

# Frontend setup
cd ../frontend
npm install
```

## Coding Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints for all functions
- Use async/await for I/O operations
- Run `ruff check .` before committing
- Write docstrings for public functions

```python
async def get_user(user_id: int) -> User:
    """
    Retrieve a user by ID.

    Args:
        user_id: The unique identifier of the user.

    Returns:
        The User object if found.

    Raises:
        HTTPException: If user is not found.
    """
    ...
```

### TypeScript (Frontend)

- Use strict TypeScript mode
- Prefer functional components with hooks
- Use named exports
- Follow React best practices

```typescript
export function UserProfile({ userId }: UserProfileProps): JSX.Element {
  // Component implementation
}
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

## Documentation

- Update README.md for significant changes
- Add docstrings to Python functions
- Add JSDoc comments to TypeScript functions
- Update API documentation for endpoint changes

## Questions?

Feel free to open an issue with the `question` label or reach out to the maintainers.
