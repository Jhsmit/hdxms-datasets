#!/bin/bash
# Run all tests with pytest

echo "Running HDX-MS Dataset Builder Backend Tests..."
echo ""

# Install dev dependencies if needed
if ! python -c "import pytest" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install -e ".[dev]"
    echo ""
fi

# Run tests
pytest

# Show coverage if available
if python -c "import pytest_cov" 2>/dev/null; then
    echo ""
    echo "Running with coverage..."
    pytest --cov=app --cov-report=term-missing
fi
