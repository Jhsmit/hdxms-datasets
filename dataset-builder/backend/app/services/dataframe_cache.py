"""Dataframe caching for data files."""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from collections import OrderedDict
import narwhals as nw
from hdxms_datasets.loader import BACKEND


class DataframeCache:
    """Manages cached dataframes for uploaded data files with LRU eviction."""

    def __init__(self, max_size: int = 100):
        """
        Initialize the dataframe cache.

        Args:
            max_size: Maximum number of dataframes to cache (default: 100)
        """
        self.max_size = max_size
        # LRU cache: OrderedDict maintains insertion/access order
        # Key format: "session_id:file_id"
        self._cache: OrderedDict[str, Any] = OrderedDict()
        # Track loading operations to prevent duplicate loads
        self._loading: Dict[str, asyncio.Event] = {}
        # Track which session owns which keys for session-level operations
        self._session_keys: Dict[str, set[str]] = {}

    async def get_dataframe(self, session_id: str, file_id: str, file_path: Path) -> Optional[Any]:
        """
        Get a cached dataframe or load it if not cached (LRU).

        Args:
            session_id: Session identifier
            file_id: File identifier
            file_path: Path to the data file

        Returns:
            The loaded dataframe or None if loading fails
        """
        cache_key = f"{session_id}:{file_id}"

        # Check if already cached and move to end (most recently used)
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        # Check if already loading - wait for it to complete
        if cache_key in self._loading:
            await self._loading[cache_key].wait()
            # After waiting, check cache again
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                return self._cache[cache_key]
            return None

        # Start loading
        self._loading[cache_key] = asyncio.Event()

        try:
            # Load dataframe asynchronously in thread pool
            df = await asyncio.to_thread(self._load_dataframe, file_path)

            # Evict least recently used item if at capacity
            if len(self._cache) >= self.max_size:
                # Remove the first (oldest) item
                evicted_key, _ = self._cache.popitem(last=False)
                # Clean up session tracking
                evicted_session = evicted_key.split(':', 1)[0]
                if evicted_session in self._session_keys:
                    self._session_keys[evicted_session].discard(evicted_key)
                    if not self._session_keys[evicted_session]:
                        del self._session_keys[evicted_session]
                print(f"LRU eviction: removed {evicted_key} (cache size: {len(self._cache)})")

            # Cache the result
            self._cache[cache_key] = df

            # Track session ownership
            if session_id not in self._session_keys:
                self._session_keys[session_id] = set()
            self._session_keys[session_id].add(cache_key)

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
            if session_id in self._session_keys:
                keys_to_remove = list(self._session_keys[session_id])
                for key in keys_to_remove:
                    if key in self._cache:
                        del self._cache[key]
                del self._session_keys[session_id]
        else:
            # Clear specific file cache
            cache_key = f"{session_id}:{file_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]
            if session_id in self._session_keys:
                self._session_keys[session_id].discard(cache_key)
                if not self._session_keys[session_id]:
                    del self._session_keys[session_id]

    def get_cached_file_ids(self, session_id: str) -> list[str]:
        """
        Get list of file IDs that have cached dataframes.

        Args:
            session_id: Session identifier

        Returns:
            List of file IDs with cached dataframes
        """
        if session_id not in self._session_keys:
            return []
        # Extract file_id from cache keys (format: "session_id:file_id")
        return [key.split(':', 1)[1] for key in self._session_keys[session_id]]

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "sessions": len(self._session_keys),
            "loading": len(self._loading)
        }


# Global dataframe cache instance
dataframe_cache = DataframeCache()
