# HDX-MS Dataset Builder - Backend

FastAPI backend for the HDX-MS Dataset Builder application.

## Setup

1. Install dependencies:
```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

2. Run the development server:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── files.py      # File upload/management
│   │   ├── validation.py # Validation endpoints
│   │   └── generation.py # Dataset generation
│   ├── models/           # Pydantic models
│   │   └── api_models.py # API request/response models
│   ├── services/         # Business logic
│   │   ├── session_manager.py
│   │   └── file_manager.py
│   └── main.py          # FastAPI app
├── tests/               # Test files
└── pyproject.toml       # Dependencies
```

## API Endpoints

### Session Management
- `POST /api/files/session` - Create a new session

### File Management
- `POST /api/files/upload` - Upload a data or structure file
- `DELETE /api/files/{file_id}` - Delete a file
- `GET /api/files/list` - List all uploaded files

### Validation
- `POST /api/validate/state` - Validate a state configuration
- `POST /api/validate/protein` - Validate protein identifiers
- `POST /api/validate/metadata` - Validate metadata

### Generation
- `POST /api/generate/json` - Generate dataset.json
- `POST /api/generate/package` - Generate ZIP package (TODO)

## Development

### Running Tests

Run all tests:
```bash
# Quick way
./run_tests.sh  # Linux/Mac
run_tests.bat   # Windows

# Or manually
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_file_upload.py

# Verbose output
pytest -v
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

### Test Statistics
- **~40 tests** covering all major functionality
- Tests for file upload, validation, sessions, and API endpoints
- Automatic cleanup of test data

Format code:
```bash
black app/
```

## Environment Variables

- `CORS_ORIGINS` - Comma-separated list of allowed origins (default: http://localhost:5173,http://localhost:3000)
- `SESSION_EXPIRY_HOURS` - Session expiration time (default: 24)
