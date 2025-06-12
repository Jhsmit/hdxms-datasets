import textwrap

from hdxms_datasets.datasets import DataSet, allow_missing_fields
from hdxms_datasets.datavault import DataVault
from pathlib import Path
import pytest
import yaml
import narwhals as nw

TEST_PTH = Path(__file__).parent
DATA_ID = "1745478702_hd_examiner_example_Sharpe"


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
    assert list(dataset.states.keys()) == ["D90", "D80", "D60", "D70"]
    assert set(dataset.peptides_per_state["D90"]) == set(
        [
            "partially_deuterated",
            "fully_deuterated",
            "non_deuterated",
        ]
    )
    assert set(dataset.peptides_per_state["D80"]) == set(
        [
            "partially_deuterated",
            "fully_deuterated",
            "non_deuterated",
        ]
    )

    df = dataset.states["D90"].peptides["partially_deuterated"].load()
    assert isinstance(df, nw.DataFrame)
    assert len(df) == 244

    fd_control = dataset.states["D90"].peptides["fully_deuterated"].load()
    assert len(fd_control) == 61

    nd_control = dataset.states["D90"].peptides["non_deuterated"].load()
    assert len(nd_control) == 61

    s = """
    D90:
      fully_deuterated: 'Total peptides: 61, timepoints: FD'
      non_deuterated: 'Total peptides: 61, timepoints: 0.0'
      partially_deuterated: 'Total peptides: 244, timepoints: 15.0, 150.0, 1500.0, 15000.0'
    D80:
      fully_deuterated: 'Total peptides: 61, timepoints: FD'
      non_deuterated: 'Total peptides: 61, timepoints: 0.0'
      partially_deuterated: 'Total peptides: 244, timepoints: 15.0, 150.0, 1500.0, 15000.0'
    D60:
      fully_deuterated: 'Total peptides: 61, timepoints: FD'
      non_deuterated: 'Total peptides: 61, timepoints: 0.0'
      partially_deuterated: 'Total peptides: 244, timepoints: 15.0, 150.0, 1500.0, 15000.0'
    D70:
      fully_deuterated: 'Total peptides: 61, timepoints: FD'
      non_deuterated: 'Total peptides: 61, timepoints: 0.0'
      partially_deuterated: 'Total peptides: 244, timepoints: 15.0, 150.0, 1500.0, 15000.0'
    """

    assert textwrap.dedent(s.lstrip("\n")) == dataset.describe()
