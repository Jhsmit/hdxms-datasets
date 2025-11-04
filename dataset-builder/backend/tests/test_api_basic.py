"""Basic API endpoint tests."""
import pytest


def test_root_endpoint(client):
    """Test the root endpoint returns correct info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "HDX-MS Dataset Builder API"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_cors_headers(client):
    """Test that CORS headers are present."""
    response = client.options(
        "/api/files/upload",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST"
        }
    )
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers
