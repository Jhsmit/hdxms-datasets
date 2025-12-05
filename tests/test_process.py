from pathlib import Path
import polars as pl

# pytest.skip("Disabled pending refactor", allow_module_level=True)

from polars.testing import assert_frame_equal
import pytest

from hdxms_datasets.database import DataBase
from hdxms_datasets.process import merge_peptides, compute_uptake_metrics


TEST_PTH = Path(__file__).parent
DATA_ID_CLUSTER_SECA = "HDX_3BAE2080"
DATA_ID_STATE_SECA = "HDX_C1198C76"


db = DataBase(TEST_PTH / "datasets")
TEST_DATASET_IDS = ["HDX_C1198C76", "HDX_3BAE2080", "HDX_2E335A82"]


@pytest.mark.parametrize("dataset_id", TEST_DATASET_IDS)
def test_load_convert(dataset_id):
    """Load and compare to saved result"""
    dataset = db.load_dataset(dataset_id)

    state = dataset.get_state(0)
    merged = merge_peptides(state.peptides)
    df_test = compute_uptake_metrics(merged, exception="ignore").to_native()

    df_ref = pl.read_parquet(TEST_PTH / "test_data" / f"{dataset_id}_state_0_processed.pq")

    assert_frame_equal(df_test, df_ref)
