# Tools Module API

A FastAPI-based dynamic tool registry and execution system for intelligent agents. This module allows tools to be added, removed, and configured without code changes, with comprehensive permission and rate limiting support.

## Features

- Dynamic tool registry (HTTP and Database tools)
- Role-based permission system
- Rate limiting per tool
- Execution history and analytics
- REST API for all operations

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip or poetry

### Installation

1. Clone the repository and navigate to the project directory

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file and configure:
```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

5. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Health Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

## Development

### Running with auto-reload:
```bash
uvicorn app.main:app --reload
```

### Running tests:
```bash
pytest
```

## Project Structure

```
tools-module/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration settings
│   ├── database/            # Database models and migrations
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   ├── executors/           # Tool execution engines
│   ├── middleware/          # Auth, permissions, rate limiting
│   └── schemas/             # Pydantic models
├── tests/                   # Test files
├── requirements.txt
├── .env.example
└── README.md
```

## License

MIT

