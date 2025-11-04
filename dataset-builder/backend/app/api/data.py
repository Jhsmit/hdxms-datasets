"""Data file and dataframe endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path to import hdxms_datasets
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.services import file_manager, session_manager, dataframe_cache

router = APIRouter()


@router.get("/dataframe/{file_id}")
async def get_dataframe(file_id: str, session_id: str):
    """
    Get a dataframe for a data file.

    Args:
        file_id: File identifier
        session_id: Session identifier

    Returns:
        Dictionary with dataframe info (shape, columns, preview)
    """
    # Validate session
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if file exists in session
    if "files" not in session or file_id not in session["files"]:
        raise HTTPException(status_code=404, detail="File not found")

    file_info = session["files"][file_id]

    # Only data files can have dataframes
    if file_info["file_type"] != "data":
        raise HTTPException(status_code=400, detail="Only data files have dataframes")

    # Get file path
    file_path = file_manager.get_file_path(session_id, file_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Get or load dataframe from cache
    df = await dataframe_cache.get_dataframe(session_id, file_id, file_path)
    if df is None:
        raise HTTPException(status_code=500, detail="Failed to load dataframe")

    # Convert dataframe info to JSON-serializable format
    try:
        # Get basic info
        shape = df.shape
        columns = df.columns

        return {
            "file_id": file_id,
            "shape": {"rows": shape[0], "columns": shape[1]},
            "columns": columns,
        }
    except Exception as e:
        import traceback

        print(f"Error serializing dataframe: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to serialize dataframe: {str(e)}")


@router.get("/dataframe/columns/{file_id}")
async def get_dataframe_columns(file_id: str, session_id: str):
    """
    Get column names for a data file.

    Args:
        file_id: File identifier
        session_id: Session identifier

    Returns:
        List of column names
    """
    # Validate session
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if file exists in session
    if "files" not in session or file_id not in session["files"]:
        raise HTTPException(status_code=404, detail="File not found")

    file_info = session["files"][file_id]

    # Only data files can have dataframes
    if file_info["file_type"] != "data":
        raise HTTPException(status_code=400, detail="Only data files have dataframes")

    # Get file path
    file_path = file_manager.get_file_path(session_id, file_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Get or load dataframe from cache
    df = await dataframe_cache.get_dataframe(session_id, file_id, file_path)
    if df is None:
        raise HTTPException(status_code=500, detail="Failed to load dataframe")

    return {"columns": df.columns}


@router.get("/dataframe/unique-values/{file_id}/{column_name}")
async def get_unique_values(file_id: str, column_name: str, session_id: str):
    """
    Get unique values for a column in a data file.

    Args:
        file_id: File identifier
        column_name: Column name
        session_id: Session identifier

    Returns:
        List of unique values
    """
    # Validate session
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if file exists in session
    if "files" not in session or file_id not in session["files"]:
        raise HTTPException(status_code=404, detail="File not found")

    file_info = session["files"][file_id]

    # Only data files can have dataframes
    if file_info["file_type"] != "data":
        raise HTTPException(status_code=400, detail="Only data files have dataframes")

    # Get file path
    file_path = file_manager.get_file_path(session_id, file_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Get or load dataframe from cache
    df = await dataframe_cache.get_dataframe(session_id, file_id, file_path)
    if df is None:
        raise HTTPException(status_code=500, detail="Failed to load dataframe")

    # Check if column exists
    if column_name not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{column_name}' not found")

    try:
        # Get unique values
        unique_vals = df[column_name].unique().to_list()
        return {"column": column_name, "unique_values": unique_vals}
    except Exception as e:
        import traceback

        print(f"Error getting unique values: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get unique values: {str(e)}")
