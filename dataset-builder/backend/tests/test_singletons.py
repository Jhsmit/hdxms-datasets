"""Test that service singletons are working correctly."""
import pytest
from app.services import session_manager, file_manager, SessionManager, FileManager


def test_session_manager_is_singleton():
    """Test that session_manager is the singleton instance, not the class."""
    # session_manager should be an instance
    assert isinstance(session_manager, SessionManager)

    # It should not be the class itself
    assert session_manager is not SessionManager

    # It should have the methods we expect
    assert hasattr(session_manager, 'create_session')
    assert hasattr(session_manager, 'get_session')
    assert hasattr(session_manager, '_sessions')


def test_file_manager_is_singleton():
    """Test that file_manager is the singleton instance, not the class."""
    # file_manager should be an instance
    assert isinstance(file_manager, FileManager)

    # It should not be the class itself
    assert file_manager is not FileManager

    # It should have the methods we expect
    assert hasattr(file_manager, 'save_file')
    assert hasattr(file_manager, 'get_file_path')
    assert hasattr(file_manager, 'delete_file')


def test_session_manager_singleton_persistence():
    """Test that the singleton instance maintains state across imports."""
    # Create a session
    session_id = session_manager.create_session()

    # Import again
    from app.services import session_manager as sm2

    # Should be the same instance
    assert session_manager is sm2

    # Session should still exist
    session = sm2.get_session(session_id)
    assert session is not None


def test_file_manager_singleton_persistence():
    """Test that the file manager singleton maintains state across imports."""
    # Get reference to file manager
    fm1 = file_manager

    # Import again
    from app.services import file_manager as fm2

    # Should be the same instance
    assert fm1 is fm2


def test_session_manager_shared_state():
    """Test that modifications to session_manager are visible everywhere."""
    # Clear all sessions first
    session_manager._sessions.clear()

    # Create a session
    session_id = session_manager.create_session()

    # Import in different way
    from app.services import session_manager as sm

    # Should see the same session
    assert session_id in sm._sessions
    assert len(sm._sessions) == 1


def test_can_create_new_instances_if_needed():
    """Test that we can still create new instances of the classes if needed."""
    # We can create new instances for testing
    new_sm = SessionManager(expiry_hours=1)
    new_fm = FileManager()

    # They should be different from the singletons
    assert new_sm is not session_manager
    assert new_fm is not file_manager

    # They should still work
    test_session_id = new_sm.create_session()
    assert test_session_id is not None
