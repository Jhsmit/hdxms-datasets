import textwrap

from hdxms_datasets.datasets import DataSet, create_dataset
from hdxms_datasets.datavault import DataVault
from pathlib import Path
import pytest
import yaml
import pandas as pd
import numpy as np

TEST_PTH = Path(__file__).parent
DATA_ID = "1665149400_SecA_Krishnamurthy"


@pytest.fixture()
def hdx_spec():
    hdx_spec = yaml.safe_load((TEST_PTH / "datasets" / DATA_ID / "hdx_spec.yaml").read_text())

    yield hdx_spec


@pytest.fixture()
def dataset():
    vault = DataVault(cache_dir=TEST_PTH / "datasets")
    ds = vault.load_dataset(DATA_ID)
    yield ds


def test_dataset(dataset: DataSet):
    assert isinstance(dataset, DataSet)
    assert dataset.states == ["SecA_monomer", "SecA_monomer_ADP", "SecA_WT"]
    assert dataset.peptides_per_state["SecA_monomer"] == ["FD_control", "experiment"]
    assert dataset.peptides_per_state["SecA_monomer_ADP"] == ["FD_control", "experiment"]
    assert dataset.peptides_per_state["SecA_WT"] == ["FD_control", "experiment"]

    df = dataset.peptide_sets["SecA_monomer"]["experiment"]
    assert isinstance(df, pd.DataFrame)

    df_control = dataset.peptide_sets["SecA_monomer"]["FD_control"]
    assert len(df_control) == 188

    df_control = dataset.peptide_sets["SecA_WT"]["FD_control"]
    assert len(df_control) == 188

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
      FD_control: 'Total peptides: 188, timepoints: 1'
      experiment: 'Total peptides: 1316, timepoints: 7'
      metadata: 'Temperature: 20.0 C, pH: 7.5'
    """

    assert textwrap.dedent(s.lstrip("\n")) == dataset.describe()


def test_create_dataset(tmp_path):
    author_name = "smit"
    human_readable_tag = "testing"  # optional tag

    data_id = create_dataset(tmp_path / "datasets", author_name, human_readable_tag)

    dataset_pth = tmp_path / "datasets" / data_id

    assert human_readable_tag == data_id.split("_")[1]
    assert author_name == data_id.split("_")[2]

    assert (dataset_pth / "readme.md").read_text() == f"# {data_id}"

    assert (dataset_pth / "hdx_spec.yaml").exists()
    assert (dataset_pth / "data" / "data_file.csv").exists()


def test_metadata(dataset: DataSet):
    test_metadata = yaml.safe_load((TEST_PTH / "datasets" / DATA_ID / "metadata.yaml").read_text())
    assert dataset.metadata == test_metadata
    assert dataset.metadata["authors"][0]["name"] == "Srinath Krishnamurthy"


def test_empty_vault(tmp_path):
    vault = DataVault(cache_dir=tmp_path)
    assert len(vault.datasets) == 0

    idx = vault.remote_index
    assert len(idx) > 0

    assert vault.fetch_dataset(DATA_ID)
    assert DATA_ID in vault.datasets

    ds = vault.load_dataset(DATA_ID)

    vault.clear_cache()
    assert len(vault.datasets) == 0


def test_vault():
    vault = DataVault(cache_dir=TEST_PTH / "datasets")
    assert len(vault.datasets) == 1

    ds = vault.load_dataset(DATA_ID)
    assert isinstance(ds, DataSet)

    states = ds.states
    assert states == ["SecA_monomer", "SecA_monomer_ADP", "SecA_WT"]

    peptide_dict = ds.load_state(states[0])
    assert "experiment" in peptide_dict

    df = peptide_dict["experiment"]
    ref_df = pd.read_csv(TEST_PTH / "test_data" / "monomer_experimental_peptides.csv", index_col=0)

    pd.testing.assert_frame_equal(df, ref_df)
