from pathlib import Path
import polars as pl
import pytest

from hdxms_datasets.datasets import DataSet, allow_missing_fields
from hdxms_datasets.datavault import DataVault
from polars.testing import assert_frame_equal


TEST_PTH = Path(__file__).parent


# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(TEST_PTH / "datasets")


@pytest.fixture
def cluster_data() -> DataSet:
    return vault.load_dataset("1744801204_SecA_cluster_Krishnamurthy")


def test_load_convert_cluster():
    with allow_missing_fields():
        ds = vault.load_dataset("1744801204_SecA_cluster_Krishnamurthy")

    df_test = ds.get_state(0).compute_uptake_metrics().to_native()
    df_ref = pl.read_parquet(TEST_PTH / "test_data" / "dynamx_cluster.pq")

    assert_frame_equal(df_test, df_ref)


def test_load_convert_state():
    with allow_missing_fields():
        ds = vault.load_dataset("1665149400_SecA_Krishnamurthy")
    df_test = ds.get_state(0).compute_uptake_metrics().to_native()
    df_ref = pl.read_parquet(TEST_PTH / "test_data" / "dynamx_state.pq")

    assert_frame_equal(df_test, df_ref)


def test_load_convert_hdexaminer():
    with allow_missing_fields():
        ds = vault.load_dataset("1745478702_hd_examiner_example_Sharpe")
    df_test = ds.get_state(0).compute_uptake_metrics().to_native()
    df_ref = pl.read_parquet(TEST_PTH / "test_data" / "hd_examiner.pq")

    assert_frame_equal(df_test, df_ref)
