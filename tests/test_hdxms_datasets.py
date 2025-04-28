import textwrap

from hdxms_datasets.datasets import DataSet, create_dataset
from hdxms_datasets.datavault import DataVault, RemoteDataVault
from pathlib import Path
import pytest
import yaml
import polars as pl
import narwhals as nw
from polars.testing import assert_frame_equal

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
    assert dataset.peptides_per_state["SecA_monomer"] == [
        "fully_deuterated",
        "partially_deuterated",
    ]
    assert dataset.peptides_per_state["SecA_monomer_ADP"] == [
        "fully_deuterated",
        "partially_deuterated",
    ]
    assert dataset.peptides_per_state["SecA_WT"] == ["fully_deuterated", "partially_deuterated"]

    df = dataset.peptides["SecA_monomer", "partially_deuterated"].load()
    assert isinstance(df, nw.DataFrame)

    df_control = dataset["SecA_monomer", "fully_deuterated"].load()
    assert len(df_control) == 188

    df_control = dataset.peptides["SecA_WT", "fully_deuterated"].load()
    assert len(df_control) == 188

    s = """
    SecA_monomer:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1273, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    SecA_monomer_ADP:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1267, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    SecA_WT:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1316, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
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


TEST_URL = "https://raw.githubusercontent.com/Jhsmit/hdxms-datasets/tree/master/tests/datasets"


def test_fetch_dataset_vault(tmp_path):
    vault = RemoteDataVault(cache_dir=tmp_path, remote_url=TEST_URL)
    assert len(vault.datasets) == 0

    assert vault.fetch_dataset(DATA_ID)
    assert DATA_ID in vault.datasets

    ds = vault.load_dataset(DATA_ID)
    assert isinstance(ds, DataSet)

    vault.clear_cache()
    assert len(vault.datasets) == 0


def test_vault():
    vault = DataVault(cache_dir=TEST_PTH / "datasets")
    assert len(vault.datasets) == 3

    ds = vault.load_dataset(DATA_ID)
    assert isinstance(ds, DataSet)

    states = ds.states
    assert states == ["SecA_monomer", "SecA_monomer_ADP", "SecA_WT"]

    key = ("SecA_monomer", "partially_deuterated")
    assert key in ds.peptides

    df = ds[key].load()
    assert isinstance(df, nw.DataFrame)
    ref_df = pl.read_csv(TEST_PTH / "test_data" / "monomer_experimental_peptides.csv")

    print("TODO fix this test")
    # assert_frame_equal(df.to_polars(), ref_df[:, 1:])
