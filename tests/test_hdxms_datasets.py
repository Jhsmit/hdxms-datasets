import textwrap

from hdxms_datasets.datasets import HDXDataSet
from hdxms_datasets.datavault import DataVault
from pathlib import Path
import pytest
import yaml
import pandas as pd
import numpy as np

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
        assert dataset.peptides_per_state["SecA_monomer"] == ["FD_control", "experiment"]
        assert dataset.peptides_per_state["SecA_monomer_ADP"] == ["FD_control", "experiment"]
        assert dataset.peptides_per_state["SecA_WT"] == ["FD_control", "experiment"]

        df = dataset.peptide_sets["SecA_monomer"]["experiment"]
        assert isinstance(df, pd.DataFrame)

        df_control = dataset.peptide_sets["SecA_monomer"]["FD_control"]
        assert len(df_control) == 188

        # Control with two peptides removed
        df_control = dataset.peptide_sets["SecA_WT"]["FD_control"]
        assert len(df_control) == 186
        assert "TKVFGSRND" not in df["sequence"]
        assert not np.any(np.logical_and(df["start"] == 16, df["end"] == 29))

        s = """
        SecA_monomer:
          FD_control: 'Total peptides: 188, timepoints: 1'
          experiment: 'Total peptides: 1273, timepoints: 7'
          metadata: 'Temperature: 20.0 C, pH: 7.5'
        SecA_monomer_ADP:
          FD_control: 'Total peptides: 188, timepoints: 1'
          experiment: 'Total peptides: 1267, timepoints: 7'
          metadata: 'Temperature: 20.0 C, pH: 7.5'
        SecA_WT:
          FD_control: 'Total peptides: 186, timepoints: 1'
          experiment: 'Total peptides: 1316, timepoints: 7'
          metadata: 'Temperature: 20.0 C, pH: 7.5'
        """

        assert textwrap.dedent(s.lstrip("\n")) == dataset.describe()

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
