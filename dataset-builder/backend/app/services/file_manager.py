"""File management for uploaded files."""

import shutil
import uuid
from pathlib import Path
from typing import Optional
import tempfile


class FileManager:
    """Manages temporary file storage for sessions."""

    def __init__(self):
        self.temp_root = Path(tempfile.gettempdir()) / "hdxms_builder"
        self.temp_root.mkdir(exist_ok=True)

    def get_session_dir(self, session_id: str) -> Path:
        """Get or create the directory for a session."""
        session_dir = self.temp_root / session_id
        session_dir.mkdir(exist_ok=True, parents=True)
        return session_dir

    def save_file(self, session_id: str, file_content: bytes, filename: str) -> tuple[str, Path]:
        """
        Save an uploaded file.

        Returns:
            Tuple of (file_id, file_path)
        """
        session_dir = self.get_session_dir(session_id)
        file_id = str(uuid.uuid4())

        # Preserve original filename in subdirectory
        file_dir = session_dir / file_id
        file_dir.mkdir(exist_ok=True)
        file_path = file_dir / filename

        file_path.write_bytes(file_content)

        return file_id, file_path

    def get_file_path(self, session_id: str, file_id: str) -> Optional[Path]:
        """Get the path to a file by its ID."""
        session_dir = self.get_session_dir(session_id)
        file_dir = session_dir / file_id

        if not file_dir.exists():
            return None

        # Find the file in the directory (should be only one)
        files = list(file_dir.glob("*"))
        if files:
            return files[0]
        return None

    def delete_file(self, session_id: str, file_id: str) -> bool:
        """Delete a file by its ID."""
        session_dir = self.get_session_dir(session_id)
        file_dir = session_dir / file_id

        if file_dir.exists():
            shutil.rmtree(file_dir)
            return True
        return False

    def cleanup_session(self, session_id: str):
        """Delete all files for a session."""
        session_dir = self.get_session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)


# Global file manager instance
file_manager = FileManager()
