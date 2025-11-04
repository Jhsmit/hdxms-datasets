"""File manager service tests."""
import pytest
from pathlib import Path
from app.services import file_manager


def test_create_session_directory():
    """Test creating a session directory."""
    session_id = "test-session-123"
    session_dir = file_manager.get_session_dir(session_id)

    assert session_dir.exists()
    assert session_dir.is_dir()
    assert session_id in str(session_dir)


def test_save_file():
    """Test saving a file."""
    session_id = "test-session-save"
    content = b"Test file content"
    filename = "test.txt"

    file_id, file_path = file_manager.save_file(session_id, content, filename)

    assert file_id is not None
    assert file_path.exists()
    assert file_path.read_bytes() == content
    assert file_path.name == filename


def test_get_file_path():
    """Test retrieving file path."""
    session_id = "test-session-get"
    content = b"Test content"
    filename = "test.txt"

    file_id, saved_path = file_manager.save_file(session_id, content, filename)

    # Get file path
    retrieved_path = file_manager.get_file_path(session_id, file_id)

    assert retrieved_path == saved_path
    assert retrieved_path.exists()


def test_get_nonexistent_file_path():
    """Test getting path for non-existent file."""
    session_id = "test-session-nonexistent"
    file_id = "nonexistent-file"

    file_path = file_manager.get_file_path(session_id, file_id)
    assert file_path is None


def test_delete_file():
    """Test deleting a file."""
    session_id = "test-session-delete"
    content = b"Test content"
    filename = "test.txt"

    file_id, file_path = file_manager.save_file(session_id, content, filename)
    assert file_path.exists()

    # Delete file
    success = file_manager.delete_file(session_id, file_id)
    assert success is True

    # File should no longer exist
    assert not file_path.exists()


def test_cleanup_session():
    """Test cleaning up all files in a session."""
    session_id = "test-session-cleanup"

    # Create multiple files
    for i in range(3):
        content = f"Test content {i}".encode()
        filename = f"test_{i}.txt"
        file_manager.save_file(session_id, content, filename)

    session_dir = file_manager.get_session_dir(session_id)
    assert session_dir.exists()

    # Cleanup session
    file_manager.cleanup_session(session_id)

    # Session directory should be gone
    assert not session_dir.exists()


def test_multiple_sessions_isolated():
    """Test that files in different sessions are isolated."""
    session1_id = "test-session-1"
    session2_id = "test-session-2"

    content = b"Test content"
    filename = "test.txt"

    # Save files in different sessions
    file1_id, path1 = file_manager.save_file(session1_id, content, filename)
    file2_id, path2 = file_manager.save_file(session2_id, content, filename)

    # Files should be in different directories
    assert path1.parent.parent != path2.parent.parent

    # Should be able to retrieve each file independently
    assert file_manager.get_file_path(session1_id, file1_id) == path1
    assert file_manager.get_file_path(session2_id, file2_id) == path2
