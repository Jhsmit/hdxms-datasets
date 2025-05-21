from pathlib import Path
import numpy as np
import polars as pl
import narwhals as nw
import pytest

from hdxms_datasets.datasets import DataSet
from hdxms_datasets.datavault import DataVault
from hdxms_datasets.process import (
    convert_temperature,
    dynamx_cluster_to_state,
)
from hdxms_datasets.reader import read_dynamx
from polars.testing import assert_frame_equal


TEST_PTH = Path(__file__).parent


# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(TEST_PTH / "datasets")

# Load the dataset
ds = vault.load_dataset("1744801204_SecA_cluster_Krishnamurthy")


@pytest.fixture
def cluster_data() -> DataSet:
    return vault.load_dataset("1744801204_SecA_cluster_Krishnamurthy")


def test_load_convert_cluster():
    ds = vault.load_dataset("1744801204_SecA_cluster_Krishnamurthy")
    df_test = ds.compute_uptake_metrics(0).to_native()
    df_ref = pl.read_parquet(TEST_PTH / "test_data" / "dynamx_cluster.pq")

    assert_frame_equal(df_test, df_ref)


def test_load_convert_state():
    ds = vault.load_dataset("1665149400_SecA_Krishnamurthy")
    df_test = ds.compute_uptake_metrics(0).to_native()
    df_ref = pl.read_parquet(TEST_PTH / "test_data" / "dynamx_state.pq")

    assert_frame_equal(df_test, df_ref)


def test_load_convert_hdexaminer():
    ds = vault.load_dataset("1745478702_hd_examiner_example_Sharpe")
    df_test = ds.compute_uptake_metrics(0).to_native()
    df_ref = pl.read_parquet(TEST_PTH / "test_data" / "hd_examiner.pq")

    assert_frame_equal(df_test, df_ref)
