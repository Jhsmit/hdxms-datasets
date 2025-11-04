# Backend Tests

Comprehensive pytest test suite for the HDX-MS Dataset Builder backend API.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_api_basic.py        # Basic API endpoint tests
├── test_session.py          # Session management tests
├── test_file_upload.py      # File upload/download tests
├── test_validation.py       # Validation endpoint tests
└── test_file_manager.py     # File manager service tests
```

## Running Tests

### Quick Start

**Windows:**
```bash
cd backend
run_tests.bat
```

**Linux/Mac:**
```bash
cd backend
chmod +x run_tests.sh
./run_tests.sh
```

### Manual Run

```bash
cd backend

# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_file_upload.py

# Run specific test
pytest tests/test_file_upload.py::test_upload_csv_file

# Run with coverage
pytest --cov=app --cov-report=html
```

## Test Coverage

### Current Test Modules

1. **test_api_basic.py** - Basic API functionality
   - Root endpoint
   - Health check
   - CORS headers

2. **test_session.py** - Session management
   - Session creation
   - Session retrieval
   - Session updates
   - Session deletion
   - Auto-creation on upload

3. **test_file_upload.py** - File operations
   - CSV file upload
   - PDB file upload
   - Multiple file uploads
   - File listing
   - File deletion
   - Error cases

4. **test_validation.py** - Data validation
   - Protein identifier validation
   - State validation
   - Sequence length validation
   - Metadata validation
   - ORCID format validation
   - DOI format validation

5. **test_file_manager.py** - File manager service
   - Directory creation
   - File saving
   - File retrieval
   - File deletion
   - Session cleanup
   - Session isolation

## Fixtures

### Available Fixtures

- `client` - FastAPI TestClient for making API requests
- `session_id` - A valid session ID (auto-created)
- `sample_csv_file` - Sample CSV file for testing
- `sample_pdb_file` - Sample PDB file for testing
- `cleanup_sessions` - Auto-cleanup sessions after tests
- `cleanup_temp_files` - Auto-cleanup temp files after tests

### Using Fixtures

```python
def test_example(client, session_id, sample_csv_file):
    """Test with fixtures."""
    filename, content, content_type = sample_csv_file

    response = client.post(
        "/api/files/upload",
        data={"session_id": session_id, "file_type": "data"},
        files={"file": (filename, content, content_type)}
    )

    assert response.status_code == 200
```

## Writing New Tests

### Test Naming Convention

- File names: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Example Test

```python
def test_new_feature(client, session_id):
    """Test description here."""
    # Arrange
    test_data = {"key": "value"}

    # Act
    response = client.post("/api/endpoint", json=test_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

### Best Practices

1. **Use descriptive names**
   ```python
   # Good
   def test_upload_csv_file_succeeds_with_valid_data()

   # Bad
   def test_upload()
   ```

2. **One assertion per test when possible**
   ```python
   def test_response_status():
       assert response.status_code == 200

   def test_response_data():
       assert "id" in response.json()
   ```

3. **Use fixtures for setup**
   ```python
   @pytest.fixture
   def sample_data():
       return {"test": "data"}

   def test_with_data(sample_data):
       assert sample_data["test"] == "data"
   ```

4. **Test both success and failure cases**
   ```python
   def test_upload_success(client, session_id, sample_csv_file):
       # Test successful upload
       pass

   def test_upload_fails_without_session_id(client):
       # Test failure case
       pass
   ```

## Coverage Reports

Generate HTML coverage report:

```bash
pytest --cov=app --cov-report=html
```

View report:
```bash
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=app
```

## Troubleshooting

### Import Errors

If you get import errors:
```bash
# Make sure you're in the backend directory
cd backend

# Install in editable mode
pip install -e .

# Run from backend directory
pytest
```

### Tests Hanging

If tests hang:
- Check for infinite loops
- Check for blocking I/O
- Use `pytest -x` to stop on first failure

### Cleanup Issues

If temp files aren't cleaned up:
```bash
# Manually clean
python -c "import shutil; shutil.rmtree('/tmp/hdxms_builder', ignore_errors=True)"
```

### Session Issues

If session tests fail:
- Check `cleanup_sessions` fixture is active
- Verify `session_manager._sessions` is cleared

## Test Statistics

Current test count: **~40 tests**

Coverage target: **>80%**

## Future Tests

Tests to add:
- [ ] Integration tests with actual HDX data
- [ ] Performance tests for large files
- [ ] Concurrent upload tests
- [ ] Dataset generation tests
- [ ] Error recovery tests
- [ ] Format detection accuracy tests

## Running Specific Test Categories

```bash
# Run fast tests only
pytest -m "not slow"

# Run integration tests
pytest -m integration

# Run with detailed output
pytest -vv

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Output

Example successful test run:
```
============================= test session starts ==============================
platform win32 -- Python 3.10.0, pytest-8.0.0
collected 40 items

tests/test_api_basic.py::test_root_endpoint PASSED                       [  2%]
tests/test_api_basic.py::test_health_endpoint PASSED                     [  5%]
tests/test_session.py::test_create_session PASSED                        [  7%]
...
tests/test_validation.py::test_validate_metadata_valid_doi PASSED        [100%]

============================== 40 passed in 2.45s ==============================
```

## Getting Help

- Check test output for specific errors
- Review [backend/README.md](../README.md)
- Check [TROUBLESHOOTING.md](../../TROUBLESHOOTING.md)
