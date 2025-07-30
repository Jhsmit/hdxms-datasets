from hdxms_datasets.models import HDXDataSet
from hdxms_datasets.utils import verify_sequence


def verify_dataset(dataset: HDXDataSet):
    verify_peptides(dataset)
    if not datafiles_exist(dataset):
        raise ValueError("Missing datafiles")

    if dataset.file_hash is None:
        raise ValueError("Dataset file hash is not set")


def verify_peptides(dataset: HDXDataSet):
    for state in dataset.states:
        sequence = state.protein_state.sequence
        for i, peptides in enumerate(state.peptides):
            peptide_table = peptides.load()
            try:
                mismatches = verify_sequence(
                    peptide_table, sequence, n_term=state.protein_state.n_term
                )
            except IndexError as e:
                raise IndexError(f"State: {state.name}, Peptides[{i}] has an index error: {e}")
            if mismatches:
                raise ValueError(
                    f"State: {state.name}, Peptides[{i}] does not match protein sequence, mismatches: {mismatches}"
                )


def datafiles_exist(dataset: HDXDataSet) -> bool:
    """
    Check if the data files for all peptides and structures in the dataset exist.
    """
    for state in dataset.states:
        for peptides in state.peptides:
            if not peptides.data_file.exists():
                return False
    if not dataset.structure.data_file.exists():
        return False
    return True
