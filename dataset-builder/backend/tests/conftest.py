"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil

from app.main import app
from app.services import session_manager, file_manager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def session_id(client):
    """Create a test session and return its ID."""
    response = client.post("/api/files/session")
    assert response.status_code == 200
    return response.json()["session_id"]


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    content = b"""Protein,Start,End,Sequence,Exposure,Deuteration
TestProtein,1,10,TESTSEQABC,0.0,0.0
TestProtein,1,10,TESTSEQABC,1.0,5.5
TestProtein,1,10,TESTSEQABC,10.0,8.2
"""
    return ("test_data.csv", content, "text/csv")


@pytest.fixture
def sample_pdb_file():
    """Create a minimal sample PDB file for testing."""
    content = b"""HEADER    TEST STRUCTURE
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C
END
"""
    return ("test_structure.pdb", content, "chemical/x-pdb")


@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Clean up sessions after each test."""
    yield
    # Clear all sessions
    session_manager._sessions.clear()


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temporary files after each test."""
    yield
    # Clean up temp directories
    temp_root = Path(tempfile.gettempdir()) / "hdxms_builder"
    if temp_root.exists():
        shutil.rmtree(temp_root, ignore_errors=True)
