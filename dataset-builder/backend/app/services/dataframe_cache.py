"""Dataframe caching for data files."""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import narwhals as nw
from hdxms_datasets.loader import BACKEND


class DataframeCache:
    """Manages cached dataframes for uploaded data files."""

    def __init__(self):
        # Cache structure: {session_id: {file_id: dataframe}}
        self._cache: Dict[str, Dict[str, Any]] = {}
        # Track loading operations to prevent duplicate loads
        self._loading: Dict[str, asyncio.Event] = {}

    async def get_dataframe(self, session_id: str, file_id: str, file_path: Path) -> Optional[Any]:
        """
        Get a cached dataframe or load it if not cached.

        Args:
            session_id: Session identifier
            file_id: File identifier
            file_path: Path to the data file

        Returns:
            The loaded dataframe or None if loading fails
        """
        cache_key = f"{session_id}:{file_id}"

        # Check if already cached
        if session_id in self._cache and file_id in self._cache[session_id]:
            return self._cache[session_id][file_id]

        # Check if already loading - wait for it to complete
        if cache_key in self._loading:
            await self._loading[cache_key].wait()
            # After waiting, check cache again
            if session_id in self._cache and file_id in self._cache[session_id]:
                return self._cache[session_id][file_id]
            return None

        # Start loading
        self._loading[cache_key] = asyncio.Event()

        try:
            # Load dataframe asynchronously in thread pool
            df = await asyncio.to_thread(self._load_dataframe, file_path)

            # Cache the result
            if session_id not in self._cache:
                self._cache[session_id] = {}
            self._cache[session_id][file_id] = df

            return df
        except Exception as e:
            print(f"Failed to load dataframe for {file_id}: {e}")
            return None
        finally:
            # Signal that loading is complete
            self._loading[cache_key].set()
            del self._loading[cache_key]

    def _load_dataframe(self, file_path: Path) -> Any:
        """
        Load a dataframe from a file (blocking operation).

        Args:
            file_path: Path to the data file

        Returns:
            Loaded dataframe
        """
        # Determine file format
        if file_path.suffix == ".hxms":
            from hdxms_datasets.loader import read_hxms

            hxms_result = read_hxms(file_path)
            assert "DATA" in hxms_result, "HXMS file must contain 'DATA' section"
            return hxms_result["DATA"]
        else:
            # Assume CSV
            return nw.read_csv(file_path, backend=BACKEND)

    def invalidate(self, session_id: str, file_id: Optional[str] = None):
        """
        Invalidate cached dataframes.

        Args:
            session_id: Session identifier
            file_id: Optional file identifier. If None, invalidates all files in session.
        """
        if file_id is None:
            # Clear entire session cache
            if session_id in self._cache:
                del self._cache[session_id]
        else:
            # Clear specific file cache
            if session_id in self._cache and file_id in self._cache[session_id]:
                del self._cache[session_id][file_id]

    def get_cached_file_ids(self, session_id: str) -> list[str]:
        """
        Get list of file IDs that have cached dataframes.

        Args:
            session_id: Session identifier

        Returns:
            List of file IDs with cached dataframes
        """
        if session_id not in self._cache:
            return []
        return list(self._cache[session_id].keys())


# Global dataframe cache instance
dataframe_cache = DataframeCache()
