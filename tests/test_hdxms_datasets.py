from hdxms_datasets.datasets import HDXDataSet
from hdxms_datasets.datavault import DataVault
from pathlib import Path
import pytest
import yaml
import pandas as pd

TEST_PTH = Path(__file__).parent
DATA_ID = "20221007_1530_SecA_Krishnamurthy"


@pytest.fixture()
def hdx_spec():
    hdx_spec = yaml.safe_load((TEST_PTH / "datasets" / DATA_ID / "hdx_spec.yaml").read_text())

    yield hdx_spec


@pytest.fixture()
def dataset():
    vault = DataVault(cache_dir=TEST_PTH / "datasets")
    ds = vault.load_dataset(DATA_ID)
    yield ds


class TestDataSet:
    def test_load_dataset(self, hdx_spec):
        assert "metadata" in hdx_spec.keys()
        state_spec = hdx_spec["states"]

    def test_dataset(self, dataset: HDXDataSet):
        assert isinstance(dataset, HDXDataSet)
        assert dataset.states == ["SecA_monomer", "SecA_monomer_ADP", "SecA_WT"]
        assert dataset.state_peptide_sets["SecA_monomer"] == ["FD_control", "experiment"]
        assert dataset.state_peptide_sets["SecA_monomer_ADP"] == ["FD_control", "experiment"]
        assert dataset.state_peptide_sets["SecA_WT"] == ["FD_control", "experiment"]

        df = dataset.peptide_sets["SecA_monomer"]["experiment"]
        assert isinstance(df, pd.DataFrame)

    def test_metadata(self, dataset: HDXDataSet):
        test_metadata = yaml.safe_load(
            (TEST_PTH / "datasets" / DATA_ID / "metadata.yaml").read_text()
        )
        assert dataset.metadata == test_metadata
        assert dataset.metadata["authors"][0]["name"] == "Srinath Krishnamurthy"


class TestDataVault:
    def test_empty_vault(self, tmp_path):
        vault = DataVault(cache_dir=tmp_path)
        assert len(vault.datasets) == 0

        idx = vault.remote_index
        assert len(idx) > 0

    def test_vault(self):
        vault = DataVault(cache_dir=TEST_PTH / "datasets")
        assert len(vault.datasets) == 1

        ds = vault.load_dataset(DATA_ID)
        assert isinstance(ds, HDXDataSet)
