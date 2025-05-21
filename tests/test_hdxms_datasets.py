# %%
import textwrap

from hdxms_datasets.datasets import DataSet, create_dataset
from hdxms_datasets.datavault import DataVault, RemoteDataVault
from pathlib import Path
import pytest
import yaml
import polars as pl
import polars.testing as pl_testing
import narwhals as nw


# %%

TEST_PTH = Path(__file__).parent
DATA_ID = "1665149400_SecA_Krishnamurthy"

SecA_STATES = [
    "WT ADP",
    "Monomer ADP",
    "1-834 ADP",
    "WT apo",
    "Monomer apo",
    "1-834 apo",
]

# %%


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
    assert dataset.states == SecA_STATES

    for state in dataset.states:
        peptide_types = dataset.peptides_per_state[state]
        assert set(peptide_types) == set(["fully_deuterated", "partially_deuterated"])

    df = dataset.peptides["Monomer apo", "partially_deuterated"].load()
    assert isinstance(df, nw.DataFrame)

    df_control = dataset["Monomer apo", "fully_deuterated"].load()
    assert len(df_control) == 188

    df_control = dataset.peptides["WT apo", "fully_deuterated"].load()
    assert len(df_control) == 188
    df_control = dataset.peptides["1-834 apo", "fully_deuterated"].load()

    s = """
    WT ADP:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1316, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    Monomer ADP:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1267, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    1-834 ADP:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1250, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    WT apo:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1253, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    Monomer apo:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1273, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    1-834 apo:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1253, timepoints: 10.0, 30.0, 60.0, 120.0,
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


TEST_URL = (
    "https://raw.githubusercontent.com/Jhsmit/hdxms-datasets/refs/heads/master/tests/datasets/"
)


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
    assert len(vault.datasets) == 4

    ds = vault.load_dataset(DATA_ID)
    assert isinstance(ds, DataSet)

    assert ds.states == SecA_STATES

    key = ("Monomer apo", "partially_deuterated")
    assert key in ds.peptides

    df = ds[key].load()
    assert isinstance(df, nw.DataFrame)
    df = ds[key].load()
    assert isinstance(df, nw.DataFrame)
    ref_df = pl.read_csv(TEST_PTH / "test_data" / "monomer_experimental_peptides.csv").sort(
        by=["start", "end", "exposure"]
    )

    test_df = df.to_native().sort(by=["start", "end", "exposure"])
    for col in set(test_df.columns) & set(ref_df.columns):
        pl_testing.assert_series_equal(test_df[col], ref_df[col], check_exact=True)
