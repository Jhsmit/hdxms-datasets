"""Session management tests."""

import pytest
from app.services import session_manager


def test_create_session(client):
    """Test session creation endpoint."""
    response = client.post("/api/files/session")
    assert response.status_code == 200

    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0


def test_session_manager_create():
    """Test session manager creates sessions."""
    session_id = session_manager.create_session()
    assert session_id is not None

    # Session should exist
    session = session_manager.get_session(session_id)
    assert session is not None
    assert isinstance(session, dict)


def test_session_manager_get_nonexistent():
    """Test getting a non-existent session returns None."""
    session = session_manager.get_session("nonexistent-id")
    assert session is None


def test_session_manager_update():
    """Test updating session data."""
    session_id = session_manager.create_session()

    # Update session
    success = session_manager.update_session(session_id, {"test_key": "test_value"})
    assert success is True

    # Verify update
    session = session_manager.get_session(session_id)
    assert session is not None
    assert session["test_key"] == "test_value"


def test_session_manager_delete():
    """Test deleting a session."""
    session_id = session_manager.create_session()

    # Delete session
    success = session_manager.delete_session(session_id)
    assert success is True

    # Session should no longer exist
    session = session_manager.get_session(session_id)
    assert session is None


def test_session_auto_creation_on_upload(client, sample_csv_file):
    """Test that session is auto-created if it doesn't exist during upload."""
    filename, content, content_type = sample_csv_file

    # Use a non-existent session ID
    fake_session_id = "test-session-12345"

    response = client.post(
        "/api/files/upload",
        data={"session_id": fake_session_id, "file_type": "data"},
        files={"file": (filename, content, content_type)},
    )

    # Should succeed and auto-create session
    assert response.status_code == 200

    # Session should now exist
    session = session_manager.get_session(fake_session_id)
    assert session is not None
