# %%
"""
Test module for the new Pydantic/JSON-based HDX-MS datasets API.

This replaces the old YAML-based tests with tests for the new API.
"""

from hdxms_datasets.database import DataBase, load_dataset
from hdxms_datasets.models import HDXDataSet
from pathlib import Path
import pytest
import narwhals as nw


# %%

TEST_PTH = Path(__file__).parent
DATA_ID = "HDX_C1198C76"  # SecA state data

# %%


@pytest.fixture()
def dataset():
    """Load dataset using the JSON-based API"""
    dataset_dir = TEST_PTH / "datasets" / DATA_ID
    ds = load_dataset(dataset_dir)
    yield ds


@pytest.fixture()
def database():
    """Create a database instance for testing"""
    db = DataBase(TEST_PTH / "datasets")
    yield db


def test_dataset_basic(dataset: HDXDataSet):
    """Test basic dataset loading and structure"""
    assert isinstance(dataset, HDXDataSet)

    assert len(dataset.states) == 6

    first_state = dataset.states[0]
    assert len(first_state.peptides) == 2

    assert len(dataset.states[1].peptides) == 1


def test_dataset_metadata(dataset: HDXDataSet):
    """Test dataset metadata"""
    assert dataset.metadata is not None
    assert len(dataset.metadata.authors) > 0
    assert dataset.metadata.authors[0].name == "Srinath Krishnamurthy"
    assert dataset.metadata.license == "CC0"
    assert dataset.metadata.created_date is not None


def test_database_functionality(database: DataBase):
    """Test basic database functionality"""
    # Check that we can list datasets
    datasets = database.datasets
    assert DATA_ID in datasets
    assert len(datasets) > 0

    # Check that we can load a specific dataset
    dataset = database.load_dataset(DATA_ID)
    assert isinstance(dataset, HDXDataSet)


def test_peptide_loading(dataset: HDXDataSet):
    """Test that peptides can be loaded and have expected structure"""
    state = dataset.states[0]
    peptides = state.peptides[0]

    df = peptides.load()

    # Check basic DataFrame properties
    assert isinstance(df, nw.DataFrame)
    assert len(df) > 0

    # Convert to native for more detailed checks
    native_df = df.to_native()

    # Check that basic columns exist (common to most HDX-MS data)
    expected_columns = {"start", "end", "sequence"}
    assert expected_columns.issubset(set(native_df.columns))
    assert len(native_df.columns) >= len(expected_columns)


def test_protein_state(dataset: HDXDataSet):
    """Test protein state information"""
    state = dataset.states[0]
    protein_state = state.protein_state

    # Check sequence
    assert isinstance(protein_state.sequence, str)
    assert len(protein_state.sequence) > 0

    # Check termini
    assert protein_state.n_term > 0
    assert protein_state.c_term > protein_state.n_term

    # Check sequence length matches termini
    expected_length = protein_state.c_term - protein_state.n_term + 1
    assert len(protein_state.sequence) == expected_length


def test_structure_info(dataset: HDXDataSet):
    """Test structure information"""
    if dataset.structure:
        assert dataset.structure.data_file
        assert dataset.structure.format
        # Test that structure file path exists (relative or absolute)
        assert isinstance(dataset.structure.data_file, Path)
        if dataset.structure.pdb_id:
            assert isinstance(dataset.structure.pdb_id, str)
            assert len(dataset.structure.pdb_id) > 0


def test_protein_identifiers(dataset: HDXDataSet):
    """Test protein identifier information"""
    if dataset.protein_identifiers:
        # Assert that protein identifiers exist and are valid
        assert dataset.protein_identifiers.uniprot_accession_number is not None
        assert dataset.protein_identifiers.uniprot_entry_name is not None
        assert len(dataset.protein_identifiers.uniprot_accession_number) > 0
        assert len(dataset.protein_identifiers.uniprot_entry_name) > 0


# %%
