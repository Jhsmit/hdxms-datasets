"""Data file and dataframe endpoints."""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path to import hdxms_datasets
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.services import file_manager, session_manager, dataframe_cache
from hdxms_datasets.process import apply_filters
from hdxms_datasets.formats import FORMAT_LUT

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


@router.post("/dataframe/filter-options/{file_id}")
async def get_filter_options(
    file_id: str, session_id: str, filters: Optional[Dict[str, Any]] = Body(None)
):
    """
    Get available filter options for a data file with progressive cascading behavior.

    Filter field i only affects filter fields i+1, i+2, ... (not itself or earlier fields).
    For example, with filter columns ["Protein", "State", "Exposure"]:
    - "Protein" shows all unique proteins (no filters applied)
    - "State" shows states present in selected proteins
    - "Exposure" shows exposures present in selected proteins AND states

    Args:
        file_id: File identifier
        session_id: Session identifier
        filters: Dictionary of already-applied filters (column_name -> list of values)

    Returns:
        Dictionary mapping each filter column to its available unique values
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

    # Get detected format to determine filter columns
    detected_format = file_info.get("detected_format")
    if not detected_format or detected_format not in FORMAT_LUT:
        raise HTTPException(status_code=400, detail="Unknown or missing format")

    format_spec = FORMAT_LUT[detected_format]
    filter_columns = format_spec.filter_columns

    if not filter_columns:
        return {"filter_options": {}}

    # Get file path
    file_path = file_manager.get_file_path(session_id, file_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Get or load dataframe from cache
    df_original = await dataframe_cache.get_dataframe(session_id, file_id, file_path)
    if df_original is None:
        raise HTTPException(status_code=500, detail="Failed to load dataframe")

    def convert_filter_values(col: str, values: list, df) -> list:
        """Convert string filter values to appropriate types based on column dtype."""
        if col not in df.columns or not values:
            return values

        col_dtype = str(df[col].dtype)

        # Convert string values to appropriate types
        if "int" in col_dtype.lower():
            return [int(v) if v != "inf" else float("inf") for v in values]
        elif "float" in col_dtype.lower():
            return [float(v) for v in values]
        else:
            return values

    def serialize_values(values: list) -> list:
        """Convert values to JSON-serializable strings and sort them."""
        serialized = []
        for val in values:
            if val is None:
                serialized.append(None)
            elif isinstance(val, float) and (val == float("inf") or val == float("-inf")):
                serialized.append("inf" if val > 0 else "-inf")
            else:
                serialized.append(str(val))

        # Sort the values - try numeric sort first, fall back to string sort
        try:
            # Attempt to sort numerically
            sorted_vals = sorted(
                serialized,
                key=lambda x: float(x)
                if x not in [None, "inf", "-inf"]
                else (float("inf") if x == "inf" else (float("-inf") if x == "-inf" else 0)),
            )
            return sorted_vals
        except (ValueError, TypeError):
            # Fall back to string sorting if numeric fails
            return sorted(serialized, key=lambda x: (x is None, x))

    try:
        # For each filter column, compute available options considering only EARLIER filters
        # Filter field i only affects filter fields i+1, i+2, ... (not itself or earlier fields)
        filter_options = {}

        for i, col in enumerate(filter_columns):
            if col not in df_original.columns:
                filter_options[col] = []
                continue

            # Apply only filters from columns BEFORE this one (indices 0 to i-1)
            df_filtered = df_original
            if filters and i > 0:
                # Collect filters from earlier columns only
                earlier_filters = {}
                for j in range(i):
                    earlier_col = filter_columns[j]
                    if earlier_col in filters and filters[earlier_col]:
                        # Convert to appropriate types
                        earlier_filters[earlier_col] = convert_filter_values(
                            earlier_col, filters[earlier_col], df_original
                        )

                # Apply earlier filters
                if earlier_filters:
                    df_filtered = apply_filters(df_filtered, **earlier_filters)

            # Get unique values from the filtered dataframe
            unique_vals = df_filtered[col].unique().to_list()
            filter_options[col] = serialize_values(unique_vals)

        return {"filter_options": filter_options}

    except Exception as e:
        import traceback

        print(f"Error getting filter options: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get filter options: {str(e)}")
