# Testing Guide

Comprehensive testing for the HDX-MS Dataset Builder.

## Backend Tests (pytest)

### Quick Start

```bash
cd dataset-builder/backend

# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Or use the script
./run_tests.sh  # Linux/Mac
run_tests.bat   # Windows
```

### Test Coverage

**~40 tests** covering:
- ✅ API endpoints (root, health, CORS)
- ✅ Session management (create, get, update, delete)
- ✅ File upload/download (CSV, PDB, multiple files)
- ✅ Validation (protein, state, metadata)
- ✅ File manager service
- ✅ Error handling
- ✅ Auto-cleanup

### Test Structure

```
backend/tests/
├── conftest.py              # Fixtures and configuration
├── test_api_basic.py        # Basic API tests
├── test_session.py          # Session tests
├── test_file_upload.py      # File operation tests
├── test_validation.py       # Validation tests
└── test_file_manager.py     # Service tests
```

### Running Specific Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_file_upload.py

# Specific test
pytest tests/test_file_upload.py::test_upload_csv_file

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=html

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

### Example Test Output

```
============================= test session starts ==============================
collected 40 items

tests/test_api_basic.py::test_root_endpoint PASSED                       [  2%]
tests/test_api_basic.py::test_health_endpoint PASSED                     [  5%]
tests/test_api_basic.py::test_cors_headers PASSED                        [  7%]
tests/test_session.py::test_create_session PASSED                        [ 10%]
tests/test_session.py::test_session_manager_create PASSED                [ 12%]
...
tests/test_validation.py::test_validate_metadata_valid_doi PASSED        [100%]

============================== 40 passed in 2.45s ==============================
```

## Frontend Tests (Not Yet Implemented)

### Planned Tests

```bash
cd dataset-builder/frontend

# Run unit tests
npm run test

# Run E2E tests
npm run test:e2e

# Run with coverage
npm run test:coverage
```

### Test Structure (Future)

```
frontend/tests/
├── unit/
│   ├── stores/
│   │   └── dataset.spec.ts
│   ├── components/
│   │   ├── WizardContainer.spec.ts
│   │   └── steps/
│   └── services/
│       └── api.spec.ts
└── e2e/
    ├── upload.spec.ts
    ├── wizard.spec.ts
    └── generation.spec.ts
```

### Technologies (Future)

- **Unit Tests**: Vitest
- **Component Tests**: Vue Test Utils
- **E2E Tests**: Playwright or Cypress

## Integration Tests

### Manual Testing Workflow

1. **Start backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test complete workflow**
   - Open http://localhost:5173
   - Upload files
   - Navigate through wizard
   - Generate JSON

### Automated Integration Tests (Future)

```python
# tests/test_integration.py
def test_complete_dataset_creation():
    """Test creating a complete dataset end-to-end."""
    # Upload files
    # Create states
    # Add metadata
    # Generate JSON
    # Validate output
```

## Manual Testing Checklist

### File Upload
- [ ] Upload CSV file
- [ ] Upload PDB file
- [ ] Upload multiple files
- [ ] Delete file
- [ ] Format auto-detection works

### Wizard Navigation
- [ ] Navigate forward through steps
- [ ] Navigate backward through steps
- [ ] Click step numbers to jump
- [ ] "Next" button disabled when invalid
- [ ] Progress bar updates

### State Management
- [ ] Add state
- [ ] Remove state
- [ ] Add peptide to state
- [ ] Remove peptide from state
- [ ] Edit state fields
- [ ] Validation messages appear

### Metadata
- [ ] Add author
- [ ] Remove author
- [ ] Select license
- [ ] Add publication info
- [ ] ORCID validation

### Generation
- [ ] Review shows all data
- [ ] Validation errors display
- [ ] Generate JSON succeeds
- [ ] Download JSON works
- [ ] JSON format is correct

### Auto-Save
- [ ] Data persists after refresh
- [ ] localStorage contains data
- [ ] Session ID maintained

## Performance Tests (Future)

### Load Testing

```bash
# Using locust
pip install locust
locust -f tests/locustfile.py
```

### Metrics to Test
- Upload time for large files (100MB+)
- Concurrent uploads
- Session creation rate
- JSON generation time

## Test Data

### Sample Files

Located in `tests/test_data/`:
- `sample.csv` - Example HDX data
- `sample.pdb` - Example structure
- `sample_large.csv` - Large dataset

### Creating Test Data

```python
# Generate test CSV
import pandas as pd

df = pd.DataFrame({
    'Protein': ['TestProtein'] * 10,
    'Start': range(1, 11),
    'End': range(10, 20),
    'Sequence': ['TESTSEQ'] * 10,
    'Exposure': [0.0, 1.0, 10.0] * 3 + [100.0],
    'Deuteration': [0.0, 5.5, 8.2] * 3 + [9.0]
})

df.to_csv('tests/test_data/sample.csv', index=False)
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        working-directory: ./dataset-builder/backend
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        working-directory: ./dataset-builder/backend
        run: |
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Debugging Tests

### Print Debug Info

```python
def test_with_debug(client, session_id):
    response = client.post("/api/endpoint", json={"test": "data"})

    # Print for debugging
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200
```

Run with:
```bash
pytest -s  # Show print statements
```

### Use pdb Debugger

```python
def test_with_breakpoint(client):
    import pdb; pdb.set_trace()  # Breakpoint
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

### Check Test Fixtures

```python
def test_check_fixtures(client, session_id, sample_csv_file):
    """Debug test to check fixture values."""
    print(f"Session ID: {session_id}")
    print(f"CSV file: {sample_csv_file}")

    filename, content, content_type = sample_csv_file
    print(f"Filename: {filename}")
    print(f"Content length: {len(content)}")
    print(f"Content type: {content_type}")
```

## Coverage Goals

### Current Coverage
- File upload: ~90%
- Validation: ~85%
- Session management: ~95%
- File manager: ~90%

### Target Coverage
- Overall: >80%
- Critical paths: >95%
- Error handling: >90%

## Test Best Practices

1. **Descriptive names**
   ```python
   # Good
   def test_upload_fails_with_invalid_session_id()

   # Bad
   def test_upload_error()
   ```

2. **Arrange-Act-Assert pattern**
   ```python
   def test_example():
       # Arrange
       data = {"key": "value"}

       # Act
       response = client.post("/endpoint", json=data)

       # Assert
       assert response.status_code == 200
   ```

3. **Test one thing at a time**
   ```python
   # Good - separate tests
   def test_status_code():
       assert response.status_code == 200

   def test_response_data():
       assert "id" in response.json()
   ```

4. **Use fixtures for setup**
   ```python
   @pytest.fixture
   def prepared_data():
       return {"test": "data"}

   def test_with_prepared_data(prepared_data):
       assert prepared_data["test"] == "data"
   ```

## Troubleshooting Tests

### Tests Failing

1. **Check test output**
   ```bash
   pytest -v  # Verbose output
   ```

2. **Run single test**
   ```bash
   pytest tests/test_file.py::test_specific
   ```

3. **Check fixtures**
   ```bash
   pytest --fixtures  # List all fixtures
   ```

### Import Errors

```bash
# From backend directory
pip install -e .
pytest
```

### Cleanup Issues

```bash
# Manually clean temp files
python -c "import shutil, tempfile, pathlib; shutil.rmtree(pathlib.Path(tempfile.gettempdir()) / 'hdxms_builder', ignore_errors=True)"
```

## Resources

- Backend tests: [backend/tests/README.md](backend/tests/README.md)
- pytest docs: https://docs.pytest.org/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Vue testing: https://test-utils.vuejs.org/

## Contributing Tests

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests pass
3. Add documentation
4. Update coverage reports
5. Submit PR with tests

Example:
```python
# 1. Write failing test
def test_new_feature(client):
    response = client.post("/api/new-feature")
    assert response.status_code == 200

# 2. Implement feature
# 3. Test passes
# 4. Document in README
```
