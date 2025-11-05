"""Tests for dataframe cache LRU functionality."""

import asyncio
import pytest
from pathlib import Path
from app.services.dataframe_cache import DataframeCache


@pytest.fixture
def test_csv_file(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_content = "peptide,start,end,exposure,uptake\nABCDEF,1,6,10,5.5\nGHIJKL,7,12,10,3.2\n"
    file_path = tmp_path / "test_data.csv"
    file_path.write_text(csv_content)
    return file_path


@pytest.fixture
def test_csv_files(tmp_path):
    """Create multiple temporary CSV files for testing."""
    files = []
    for i in range(5):
        csv_content = f"peptide,start,end,exposure,uptake\nPEPT{i},1,5,10,{i}.5\n"
        file_path = tmp_path / f"test_data_{i}.csv"
        file_path.write_text(csv_content)
        files.append(file_path)
    return files


@pytest.mark.asyncio
async def test_cache_basic_get_and_store(test_csv_file):
    """Test basic cache get and store functionality."""
    cache = DataframeCache(max_size=10)

    # First access - should load and cache
    df1 = await cache.get_dataframe("session1", "file1", test_csv_file)
    assert df1 is not None
    assert df1.shape[0] == 2  # 2 rows

    # Second access - should return cached version
    df2 = await cache.get_dataframe("session1", "file1", test_csv_file)
    assert df2 is not None

    # Check cache stats
    stats = cache.get_cache_stats()
    assert stats["size"] == 1
    assert stats["sessions"] == 1


@pytest.mark.asyncio
async def test_lru_eviction_order(test_csv_files):
    """Test that LRU eviction removes the least recently used item."""
    cache = DataframeCache(max_size=3)

    # Load 3 files to fill cache
    df1 = await cache.get_dataframe("session1", "file1", test_csv_files[0])
    df2 = await cache.get_dataframe("session1", "file2", test_csv_files[1])
    df3 = await cache.get_dataframe("session1", "file3", test_csv_files[2])

    assert df1 is not None
    assert df2 is not None
    assert df3 is not None
    assert cache.get_cache_stats()["size"] == 3

    # Access file1 to make it most recently used
    df1_again = await cache.get_dataframe("session1", "file1", test_csv_files[0])
    assert df1_again is not None

    # Now order is: file2 (oldest), file3, file1 (newest)
    # Load file4 - should evict file2
    df4 = await cache.get_dataframe("session1", "file4", test_csv_files[3])
    assert df4 is not None
    assert cache.get_cache_stats()["size"] == 3

    # Check that file1 and file3 are still cached
    cached_ids = cache.get_cached_file_ids("session1")
    assert "file1" in cached_ids
    assert "file3" in cached_ids
    assert "file4" in cached_ids
    assert "file2" not in cached_ids  # This should be evicted


@pytest.mark.asyncio
async def test_lru_eviction_with_access_pattern(test_csv_files):
    """Test LRU with specific access pattern."""
    cache = DataframeCache(max_size=2)

    # Load file1 and file2
    await cache.get_dataframe("session1", "file1", test_csv_files[0])
    await cache.get_dataframe("session1", "file2", test_csv_files[1])
    assert cache.get_cache_stats()["size"] == 2

    # Access file1 again (makes it most recent)
    await cache.get_dataframe("session1", "file1", test_csv_files[0])

    # Load file3 - should evict file2 (least recently used)
    await cache.get_dataframe("session1", "file3", test_csv_files[2])

    cached_ids = cache.get_cached_file_ids("session1")
    assert "file1" in cached_ids
    assert "file3" in cached_ids
    assert "file2" not in cached_ids

    # Load file4 - should evict file1 (now least recently used)
    await cache.get_dataframe("session1", "file4", test_csv_files[3])

    cached_ids = cache.get_cached_file_ids("session1")
    assert "file3" in cached_ids
    assert "file4" in cached_ids
    assert "file1" not in cached_ids


@pytest.mark.asyncio
async def test_lru_across_multiple_sessions(test_csv_files):
    """Test LRU eviction works correctly across multiple sessions."""
    cache = DataframeCache(max_size=3)

    # Load files from different sessions
    await cache.get_dataframe("session1", "file1", test_csv_files[0])
    await cache.get_dataframe("session2", "file2", test_csv_files[1])
    await cache.get_dataframe("session1", "file3", test_csv_files[2])

    assert cache.get_cache_stats()["size"] == 3
    assert cache.get_cache_stats()["sessions"] == 2

    # Load another file - should evict the oldest (session1:file1)
    await cache.get_dataframe("session2", "file4", test_csv_files[3])

    assert cache.get_cache_stats()["size"] == 3

    # Check that file1 was evicted
    session1_ids = cache.get_cached_file_ids("session1")
    session2_ids = cache.get_cached_file_ids("session2")

    assert "file1" not in session1_ids
    assert "file3" in session1_ids
    assert "file2" in session2_ids
    assert "file4" in session2_ids


@pytest.mark.asyncio
async def test_invalidate_specific_file(test_csv_files):
    """Test invalidating a specific file."""
    cache = DataframeCache(max_size=5)

    await cache.get_dataframe("session1", "file1", test_csv_files[0])
    await cache.get_dataframe("session1", "file2", test_csv_files[1])

    assert cache.get_cache_stats()["size"] == 2

    # Invalidate file1
    cache.invalidate("session1", "file1")

    assert cache.get_cache_stats()["size"] == 1
    cached_ids = cache.get_cached_file_ids("session1")
    assert "file1" not in cached_ids
    assert "file2" in cached_ids


@pytest.mark.asyncio
async def test_invalidate_entire_session(test_csv_files):
    """Test invalidating all files in a session."""
    cache = DataframeCache(max_size=5)

    await cache.get_dataframe("session1", "file1", test_csv_files[0])
    await cache.get_dataframe("session1", "file2", test_csv_files[1])
    await cache.get_dataframe("session2", "file3", test_csv_files[2])

    assert cache.get_cache_stats()["size"] == 3
    assert cache.get_cache_stats()["sessions"] == 2

    # Invalidate entire session1
    cache.invalidate("session1")

    assert cache.get_cache_stats()["size"] == 1
    assert cache.get_cache_stats()["sessions"] == 1

    session1_ids = cache.get_cached_file_ids("session1")
    session2_ids = cache.get_cached_file_ids("session2")

    assert len(session1_ids) == 0
    assert "file3" in session2_ids


@pytest.mark.asyncio
async def test_concurrent_loading(test_csv_file):
    """Test that concurrent requests for the same file don't load twice."""
    cache = DataframeCache(max_size=10)

    # Start multiple concurrent requests for the same file
    tasks = [
        cache.get_dataframe("session1", "file1", test_csv_file)
        for _ in range(5)
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(df is not None for df in results)

    # Should only be one entry in cache
    assert cache.get_cache_stats()["size"] == 1


@pytest.mark.asyncio
async def test_cache_size_limit(test_csv_files):
    """Test that cache respects max_size limit."""
    max_size = 3
    cache = DataframeCache(max_size=max_size)

    # Load more files than max_size
    for i in range(5):
        await cache.get_dataframe("session1", f"file{i}", test_csv_files[i])

    # Cache should never exceed max_size
    assert cache.get_cache_stats()["size"] == max_size

    # Only the last 3 files should be cached
    cached_ids = cache.get_cached_file_ids("session1")
    assert len(cached_ids) == max_size
    assert "file2" in cached_ids
    assert "file3" in cached_ids
    assert "file4" in cached_ids
    assert "file0" not in cached_ids
    assert "file1" not in cached_ids


@pytest.mark.asyncio
async def test_access_updates_lru_order(test_csv_files):
    """Test that accessing a cached item updates its position in LRU."""
    cache = DataframeCache(max_size=2)

    # Load two files
    await cache.get_dataframe("session1", "file1", test_csv_files[0])
    await cache.get_dataframe("session1", "file2", test_csv_files[1])

    # Access file1 multiple times
    for _ in range(3):
        await cache.get_dataframe("session1", "file1", test_csv_files[0])

    # Load file3 - should evict file2, not file1
    await cache.get_dataframe("session1", "file3", test_csv_files[2])

    cached_ids = cache.get_cached_file_ids("session1")
    assert "file1" in cached_ids  # Should still be cached
    assert "file3" in cached_ids
    assert "file2" not in cached_ids  # Should be evicted
