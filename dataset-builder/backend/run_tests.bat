@echo off
echo Running HDX-MS Dataset Builder Backend Tests...
echo.

REM Install dev dependencies if needed
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo Installing test dependencies...
    pip install -e .[dev]
    echo.
)

REM Run tests
pytest

REM Show coverage if available
python -c "import pytest_cov" 2>nul
if not errorlevel 1 (
    echo.
    echo Running with coverage...
    pytest --cov=app --cov-report=term-missing
)

pause
