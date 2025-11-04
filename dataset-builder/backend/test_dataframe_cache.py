# %%

import asyncio
from pathlib import Path
from app.services.dataframe_cache import DataframeCache
from pathlib import Path

# %%

cwd = Path(__file__).parent
root = cwd.parent

f1 = root / "dev" / "ecSecB_apo.csv"
f1.exists()

hdxms_dir = Path(
    r"C:\Users\jhsmi\repos\mine\hdxms-datasets\examples\published_datasets\HDX_295C2B19"
)

f2 = hdxms_dir / "data" / "ecDHFR_2025-09-23_MTX.hxms"
f2 = hdxms_dir / "data" / "ecDHFR_2025-09-23_TRI.hxms"
f2 = hdxms_dir / "data" / "ecDHFR_2025-09-23_APO.hxms"

f2.exists()

# %%

cache = DataframeCache()
df = cache._load_dataframe(f1)
df

# %%

shape = df.shape
columns = df.columns

# Get first few rows as preview (limit to 10 rows)
preview_df = df.head(10)
preview_data = preview_df.to_dict(as_series=False)
ans = {
    "shape": {"rows": shape[0], "columns": shape[1]},
    "columns": columns,
}
ans


# %%
# %%
async def main():
    # Create cache instance
    cache = DataframeCache()

    # Test file path - adjust this to your actual test file
    test_file = Path(
        r"C:\Users\jhsmi\repos\mine\hdxms-datasets\examples\test_data\ecDHFR\ecSecB_apo.csv"
    )

    if not test_file.exists():
        print(f"Error: Test file not found at {test_file}")
        print("Please update the test_file path in the script.")
        return

    print(f"Testing with file: {test_file}")
    print("-" * 60)

    # Test 1: Load dataframe for the first time
    print("\nTest 1: Loading dataframe for the first time...")
    session_id = "test-session-123"
    file_id = "test-file-456"

    df = await cache.get_dataframe(session_id, file_id, test_file)

    if df is not None:
        print(f"✓ Dataframe loaded successfully!")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {df.columns}")
        print(f"\nFirst 3 rows:")
        print(df.head(3))
    else:
        print("✗ Failed to load dataframe")
        return

    # Test 2: Load same dataframe again (should be cached)
    print("\n" + "-" * 60)
    print("\nTest 2: Loading same dataframe again (should use cache)...")

    df2 = await cache.get_dataframe(session_id, file_id, test_file)

    if df2 is not None:
        print(f"✓ Dataframe retrieved from cache!")
        print(f"  Shape: {df2.shape}")
        # Check if it's the same object (cached)
        print(f"  Same object in memory: {df is df2}")
    else:
        print("✗ Failed to retrieve cached dataframe")

    # Test 3: Check cached file IDs
    print("\n" + "-" * 60)
    print("\nTest 3: Checking cached file IDs...")

    cached_ids = cache.get_cached_file_ids(session_id)
    print(f"Cached file IDs for session '{session_id}': {cached_ids}")

    # Test 4: Invalidate cache for specific file
    print("\n" + "-" * 60)
    print("\nTest 4: Invalidating cache for specific file...")

    cache.invalidate(session_id, file_id)
    cached_ids_after = cache.get_cached_file_ids(session_id)
    print(f"✓ Cache invalidated")
    print(f"  Cached file IDs after invalidation: {cached_ids_after}")

    # Test 5: Load dataframe after invalidation
    print("\n" + "-" * 60)
    print("\nTest 5: Loading dataframe after cache invalidation...")

    df3 = await cache.get_dataframe(session_id, file_id, test_file)

    if df3 is not None:
        print(f"✓ Dataframe loaded again after invalidation!")
        print(f"  Shape: {df3.shape}")
        print(f"  New object in memory: {df is not df3}")
    else:
        print("✗ Failed to load dataframe after invalidation")

    # Test 6: Invalidate entire session
    print("\n" + "-" * 60)
    print("\nTest 6: Invalidating entire session cache...")

    cache.invalidate(session_id)
    cached_ids_final = cache.get_cached_file_ids(session_id)
    print(f"✓ Session cache invalidated")
    print(f"  Cached file IDs after session invalidation: {cached_ids_final}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
