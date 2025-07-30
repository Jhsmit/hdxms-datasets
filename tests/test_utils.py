"""
Test module for utility functions using the new Pydantic/JSON-based API.

This replaces the old YAML-based tests with tests for the new API.
"""

from pathlib import Path
import pytest
from hdxms_datasets.database import DataBase, load_dataset
from hdxms_datasets.utils import (
    verify_sequence,
    diff_sequence,
    reconstruct_sequence,
    contiguous_peptides,
    non_overlapping_peptides,
    peptide_redundancy,
)
import polars as pl
import numpy as np
import narwhals as nw

TEST_PTH = Path(__file__).parent
DATA_ID = "1665149400_SecA_Krishnamurthy"  # Changed to SecA dataset
SECB_DATA_ID = "1704204434_SecB_Krishnamurthy"


# Test data for sequence verification
peptide_intervals_indices = [
    (0, 8),
    (5, 12),
    (16, 21),
    (19, 25),
    (26, 28),
]

peptide_data_sequence = "SIAGIEGTQMAHCLGAYCPNILFPAAREGAMCP"
known_sequence = "SIAGIEGTTMAHCLGAYCPNILFGAAREGAMCP"

r_number_default = np.arange(1, len(peptide_data_sequence) + 1)
r_number_tag = r_number_default - 5

expected_mismatches_by_inx = [(8, "T", "Q"), (23, "G", "P")]


@pytest.fixture()
def database():
    """Create a database instance for testing"""
    return DataBase(TEST_PTH / "datasets")


@pytest.fixture()
def seca_dataset():
    """Load SecA dataset for testing"""
    dataset_dir = TEST_PTH / "datasets" / DATA_ID
    return load_dataset(dataset_dir)


@pytest.fixture()
def secb_dataset():
    """Load SecB dataset for testing"""
    dataset_dir = TEST_PTH / "datasets" / SECB_DATA_ID
    return load_dataset(dataset_dir)


# %%


@pytest.mark.parametrize("r_number", [r_number_default, r_number_tag])
def test_verify_sequence_with_mismatches(r_number):
    """Test sequence verification with known mismatches"""
    n_term = r_number[0]

    records = [
        (r_number[i0], r_number[i1 - 1], peptide_data_sequence[i0:i1])
        for i0, i1 in peptide_intervals_indices
    ]
    df = pl.DataFrame(records, schema=["start", "end", "sequence"], orient="row")

    mismatches = verify_sequence(nw.from_native(df), known_sequence, n_term)

    for mismatch, expected in zip(mismatches, expected_mismatches_by_inx):
        idx, c1, c2 = expected
        assert mismatch == (r_number[idx], c1, c2), f"Mismatch at {idx}: expected {c1}, found {c2}"


def test_verify_sequence_perfect_match():
    """Test sequence verification with perfect match"""
    records = [
        (1, 8, known_sequence[0:8]),
        (5, 12, known_sequence[4:12]),
        (16, 21, known_sequence[15:21]),
    ]
    df = pl.DataFrame(records, schema=["start", "end", "sequence"], orient="row")

    mismatches = verify_sequence(nw.from_native(df), known_sequence, n_term=1)
    assert len(mismatches) == 0


def test_secb_dataset_sequence_verification(secb_dataset):
    """Test sequence verification on real SecB dataset"""
    # Test that peptide sequences match the protein sequence
    first_state = secb_dataset.states[0]
    sequence = first_state.protein_state.sequence
    n_term = first_state.protein_state.n_term

    # Get peptides and verify sequence
    for peptides in first_state.peptides:
        if peptides.deuteration_type == "partially_deuterated":
            pd_peptides = peptides.load()
            mismatches = verify_sequence(pd_peptides, sequence, n_term=n_term)
            assert len(mismatches) == 0, f"Found sequence mismatches: {mismatches}"


def test_seca_dataset_sequence_verification(seca_dataset):
    """Test sequence verification on real SecA dataset"""
    # Test that peptide sequences match the protein sequence
    first_state = seca_dataset.states[0]
    sequence = first_state.protein_state.sequence
    n_term = first_state.protein_state.n_term

    # Get peptides and verify sequence
    for peptides in first_state.peptides:
        if peptides.deuteration_type == "partially_deuterated":
            pd_peptides = peptides.load()
            mismatches = verify_sequence(pd_peptides, sequence, n_term=n_term)
            assert len(mismatches) == 0, f"Found sequence mismatches: {mismatches}"


def test_diff_sequence():
    """Test sequence similarity calculation"""
    # Test identical sequences
    assert diff_sequence("ABCDEF", "ABCDEF") == 1.0

    # Test completely different sequences
    assert diff_sequence("ABCDEF", "GHIJKL") == 0.0

    # Test partially similar sequences
    similarity = diff_sequence("ABCDEF", "ABCDXY")
    assert 0.0 < similarity < 1.0
    assert similarity > 0.5  # Should be more than 50% similar


def test_reconstruct_sequence():
    """Test sequence reconstruction from peptides"""
    # Create simple test data
    records = [
        (1, 3, "ABC"),
        (3, 5, "CDE"),  # Overlapping peptide
        (6, 8, "FGH"),
    ]
    df = pl.DataFrame(records, schema=["start", "end", "sequence"], orient="row")

    # Use placeholder sequence
    placeholder = "X" * 8
    reconstructed = reconstruct_sequence(nw.from_native(df), placeholder, n_term=1)

    # Check that reconstructed sequence has expected parts
    assert reconstructed[0:3] == "ABC"  # First peptide
    assert reconstructed[2:5] == "CDE"  # Second peptide (overlaps at position 3)
    assert reconstructed[5:8] == "FGH"  # Third peptide


def test_contiguous_peptides():
    """Test identification of contiguous peptide regions"""
    # Create test data with some gaps
    records = [
        (1, 5, "ABCDE"),
        (6, 10, "FGHIJ"),  # Contiguous with previous
        (15, 20, "KLMNO"),  # Gap
        (21, 25, "PQRST"),  # Contiguous with previous
    ]
    df = pl.DataFrame(records, schema=["start", "end", "sequence"], orient="row")

    regions = contiguous_peptides(nw.from_native(df))

    # Should find two contiguous regions
    expected = [(1, 10), (15, 25)]
    assert regions == expected


def test_non_overlapping_peptides():
    """Test selection of non-overlapping peptides"""
    # Create test data with overlaps
    records = [
        (1, 5, "ABCDE"),
        (3, 8, "CDEFG"),  # Overlaps with first
        (10, 15, "HIJKL"),  # Non-overlapping
        (12, 18, "JKLMN"),  # Overlaps with previous
    ]
    df = pl.DataFrame(records, schema=["start", "end", "sequence"], orient="row")

    non_overlapping = non_overlapping_peptides(nw.from_native(df))

    # Should select first and third peptides (non-overlapping)
    expected = [(1, 5), (10, 15)]
    assert non_overlapping == expected


def test_peptide_redundancy():
    """Test peptide redundancy calculation"""
    # Create test data with overlapping peptides
    records = [
        (1, 3, "ABC"),  # Covers positions 1, 2 (indices 0, 1)
        (2, 4, "BCD"),  # Covers positions 2, 3 (indices 1, 2)
        (3, 5, "CDE"),  # Covers positions 3, 4 (indices 2, 3)
    ]
    df = pl.DataFrame(records, schema=["start", "end", "sequence"], orient="row")

    r_number, redundancy = peptide_redundancy(nw.from_native(df))

    # Check that arrays have correct length
    assert len(r_number) == len(redundancy)
    assert len(r_number) == 5  # Positions 1-5

    # Check redundancy values based on how searchsorted works:
    # Peptide (1,3): searchsorted gives (0,2) -> positions 1,2 get +1
    # Peptide (2,4): searchsorted gives (1,3) -> positions 2,3 get +1
    # Peptide (3,5): searchsorted gives (2,4) -> positions 3,4 get +1
    assert redundancy[0] == 1  # Position 1: only peptide 1
    assert redundancy[1] == 2  # Position 2: peptides 1 and 2
    assert redundancy[2] == 2  # Position 3: peptides 2 and 3
    assert redundancy[3] == 1  # Position 4: only peptide 3
    assert redundancy[4] == 0  # Position 5: no peptides


def test_database_functionality(database):
    """Test database utility functions"""
    # Test that database can load datasets
    datasets = database.datasets
    assert len(datasets) > 0

    # Test loading specific datasets
    for dataset_id in [DATA_ID, SECB_DATA_ID]:
        if dataset_id in datasets:
            dataset = database.load_dataset(dataset_id)
            assert dataset is not None
            assert len(dataset.states) > 0


def test_utils_with_real_data(seca_dataset):
    """Test utility functions with real peptide data"""
    first_state = seca_dataset.states[0]
    first_peptides = first_state.peptides[0]
    df = first_peptides.load()

    # Test contiguous peptides
    regions = contiguous_peptides(df)
    assert len(regions) > 0
    assert all(isinstance(region, tuple) and len(region) == 2 for region in regions)

    # Test non-overlapping peptides
    non_overlapping = non_overlapping_peptides(df)
    assert len(non_overlapping) > 0
    # Note: non_overlapping can have more regions than contiguous
    # because contiguous merges overlapping regions while non_overlapping
    # selects individual non-overlapping peptides
    assert len(non_overlapping) >= len(regions)

    # Test peptide redundancy
    r_number, redundancy = peptide_redundancy(df)
    assert len(r_number) == len(redundancy)
    assert len(r_number) > 0
    assert all(red >= 0 for red in redundancy)


# %%
