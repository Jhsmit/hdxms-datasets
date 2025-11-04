"""Session management for temporary data storage."""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class SessionManager:
    """In-memory session storage (MVP - replace with Redis/DB for production)."""

    def __init__(self, expiry_hours: int = 24):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._expiry_hours = expiry_hours

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=self._expiry_hours),
            "data": {}
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if it exists and hasn't expired."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        if datetime.now() > session["expires_at"]:
            self.delete_session(session_id)
            return None

        return session["data"]

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session["data"].update(data)
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def cleanup_expired(self):
        """Remove all expired sessions."""
        now = datetime.now()
        expired = [
            sid for sid, session in self._sessions.items()
            if now > session["expires_at"]
        ]
        for sid in expired:
            self.delete_session(sid)


# Global session manager instance
session_manager = SessionManager()
