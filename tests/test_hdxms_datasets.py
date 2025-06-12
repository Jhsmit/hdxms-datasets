# %%
import textwrap

from hdxms_datasets.datasets import DataSet, allow_missing_fields, create_dataset
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
    "SecA-WT_ADP",
    "SecA-WT_apo",
    "SecA-monomer_ADP",
    "SecA-monomer_apo",
    "SecA-1-834_ADP",
    "SecA-1-834_apo",
]

# %%


@pytest.fixture()
def hdx_spec():
    hdx_spec = yaml.safe_load((TEST_PTH / "datasets" / DATA_ID / "hdx_spec.yaml").read_text())

    yield hdx_spec


@pytest.fixture()
def dataset():
    vault = DataVault(cache_dir=TEST_PTH / "datasets")
    with allow_missing_fields():
        ds = vault.load_dataset(DATA_ID)
    yield ds


def test_dataset(dataset: DataSet):
    assert isinstance(dataset, DataSet)
    assert list(dataset.states) == SecA_STATES

    for state in dataset.states:
        peptide_types = dataset.peptides_per_state[state]
        assert set(peptide_types) == set(["fully_deuterated", "partially_deuterated"])

    state = dataset.states["SecA-monomer_apo"]
    df = state.peptides["partially_deuterated"].load()
    assert isinstance(df, nw.DataFrame)

    df_control = state.peptides["fully_deuterated"].load()
    assert len(df_control) == 188

    s = """
    SecA-WT_ADP:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1316, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    SecA-WT_apo:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1316, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    SecA-monomer_ADP:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1267, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    SecA-monomer_apo:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1273, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    SecA-1-834_ADP:
      fully_deuterated: 'Total peptides: 188, timepoints: 10.0'
      partially_deuterated: 'Total peptides: 1250, timepoints: 10.0, 30.0, 60.0, 120.0,
        300.0, 600.0, 1800.0'
    SecA-1-834_apo:
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
    with allow_missing_fields():
        ds = vault.load_dataset(DATA_ID)
    assert isinstance(ds, DataSet)

    vault.clear_cache()
    assert len(vault.datasets) == 0


def test_vault():
    vault = DataVault(cache_dir=TEST_PTH / "datasets")
    assert len(vault.datasets) == 4

    with allow_missing_fields():
        ds = vault.load_dataset(DATA_ID)
    assert isinstance(ds, DataSet)

    assert list(ds.states) == SecA_STATES

    df = ds.states["SecA-monomer_apo"].peptides["partially_deuterated"].load()
    assert isinstance(df, nw.DataFrame)

    ref_df = pl.read_csv(TEST_PTH / "test_data" / "monomer_experimental_peptides.csv").sort(
        by=["start", "end", "exposure"]
    )

    test_df = df.to_native().sort(by=["start", "end", "exposure"])
    for col in set(test_df.columns) & set(ref_df.columns):
        pl_testing.assert_series_equal(test_df[col], ref_df[col], check_exact=True)
