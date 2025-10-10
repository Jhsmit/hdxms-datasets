# %%
"""
Tests for the hdxms_datasets.database
"""

from pathlib import Path

import polars as pl
import pytest

from hdxms_datasets.database import load_dataset
from hdxms_datasets.models import HDXDataSet
from hdxms_datasets.verification import compare_structure_peptides

# %%

TEST_PTH = Path(__file__).parent
DATA_ID = "HDX_D9096080"  # SecB DynamX state data


@pytest.fixture()
def dataset():
    """Load dataset using the JSON-based API"""
    dataset_dir = TEST_PTH / "datasets" / DATA_ID
    ds = load_dataset(dataset_dir)
    yield ds


def test_compare_structure_peptides(dataset: HDXDataSet):
    """Test basic dataset loading and structure"""
    state = dataset.states[0]

    stats = compare_structure_peptides(
        dataset.structure,
        state.peptides[0],
    )
    assert stats["total_residues"] == 548
    assert stats["matched_residues"] == 495
    assert stats["identical_residues"] == 495

    dimer_state = dataset.states[1]
    stats, df = compare_structure_peptides(
        dataset.structure, dimer_state.peptides[0], returns="both"
    )

    assert stats["total_residues"] == 282
    assert stats["matched_residues"] == 255
    assert stats["identical_residues"] == 249

    df_f = df.filter(pl.col("resn_TLA") != pl.col("resn_TLA_right"))
    assert df_f.height == 6
    assert df_f["resn_TLA"].to_list() == ["ALA"] * 6
    assert df_f["resn_TLA_right"].to_list() == ["TYR", "THR", "SER"] * 2
