"""File upload and management endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pathlib import Path
from typing import Optional
import sys

from hdxms_datasets.loader import BACKEND

# Add parent directory to path to import hdxms_datasets
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.models.api_models import UploadedFileInfo
from app.services import file_manager, session_manager

router = APIRouter()


@router.post("/upload", response_model=UploadedFileInfo)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    file_type: str = Form(...),  # 'data' or 'structure'
):
    """
    Upload a data or structure file.

    Args:
        file: The file to upload
        session_id: Session identifier
        file_type: Type of file ('data' or 'structure')
    """
    try:
        # Validate session - create if doesn't exist
        session = session_manager.get_session(session_id)
        if session is None:
            # Create session with provided ID
            from datetime import datetime, timedelta

            session_manager._sessions[session_id] = {
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=24),
                "data": {},
            }
            session = session_manager.get_session(session_id)

        # Read file content
        content = await file.read()

        # Save file
        assert file.filename
        file_id, file_path = file_manager.save_file(session_id, content, file.filename)

        # Detect format for data files
        detected_format = None
        if file_type == "data":
            try:
                from hdxms_datasets.models import PeptideFormat
                import narwhals as nw

                if file_path.suffix == ".hxms":
                    detected_format = "HXMS"
                # Otherwise we assume csv and try to read and detect format
                df = nw.read_csv(file_path, backend=BACKEND)
                detected_format_obj = PeptideFormat.identify(df)
                if detected_format_obj:
                    detected_format = detected_format_obj.value
            except Exception as e:
                # If detection fails, that's okay - user can specify manually
                print(f"Format detection failed: {e}")

        # Store file info in session
        file_info = {
            "id": file_id,
            "filename": file.filename,
            "size": len(content),
            "detected_format": detected_format,
            "file_type": file_type,
            "path": str(file_path),
        }

        # Update session with file info
        if "files" not in session:
            session["files"] = {}
        session["files"][file_id] = file_info

        session_manager.update_session(session_id, session)

        return UploadedFileInfo(**file_info)

    except Exception as e:
        import traceback

        print(f"Upload error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(file_id: str, session_id: str):
    """Delete an uploaded file."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove from file system
    success = file_manager.delete_file(session_id, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove from session
    if "files" in session and file_id in session["files"]:
        del session["files"][file_id]
        session_manager.update_session(session_id, session)

    return {"message": "File deleted successfully"}


@router.get("/list")
async def list_files(session_id: str):
    """List all uploaded files for a session."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    files = session.get("files", {})
    return {"files": list(files.values())}


@router.post("/session")
async def create_session():
    """Create a new session."""
    session_id = session_manager.create_session()
    return {"session_id": session_id}
