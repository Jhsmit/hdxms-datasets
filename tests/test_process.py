from pathlib import Path
import polars as pl

# pytest.skip("Disabled pending refactor", allow_module_level=True)

from polars.testing import assert_frame_equal

from hdxms_datasets.database import DataBase
from hdxms_datasets.process import merge_peptides, compute_uptake_metrics


TEST_PTH = Path(__file__).parent
DATA_ID_CLUSTER_SECA = "HDX_3BAE2080"
DATA_ID_STATE_SECA = "HDX_C1198C76"


db = DataBase(TEST_PTH / "datasets")


def test_load_convert_cluster():
    """Load and compare to saved result"""
    dataset = db.load_dataset(DATA_ID_CLUSTER_SECA)

    state = dataset.get_state(0)
    merged = merge_peptides(state.peptides)
    df_test = compute_uptake_metrics(merged, exception="ignore").to_native()

    df_ref = pl.read_parquet(TEST_PTH / "test_data" / "HDX_3BAE2080_state_0_processed.pq")

    assert_frame_equal(df_test, df_ref)


def test_load_convert_state():
    """Load and compare to saved result"""
    dataset = db.load_dataset(DATA_ID_STATE_SECA)

    state = dataset.get_state(0)
    merged = merge_peptides(state.peptides)
    df_test = compute_uptake_metrics(merged, exception="ignore").to_native()

    df_ref = pl.read_parquet(TEST_PTH / "test_data" / f"{DATA_ID_STATE_SECA}_state_0_processed.pq")

    assert_frame_equal(df_test, df_ref)
