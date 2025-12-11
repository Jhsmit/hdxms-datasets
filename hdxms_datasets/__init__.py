"""Top-level package for HDXMS Datasets."""

from hdxms_datasets.__version__ import __version__
from hdxms_datasets.database import DataBase, RemoteDataBase, load_dataset, submit_dataset
from hdxms_datasets.formats import identify_format
from hdxms_datasets.models import (
    Author,
    DatasetMetadata,
    HDXDataSet,
    Peptides,
    ProteinIdentifiers,
    ProteinState,
    Publication,
    State,
    Structure,
)
from hdxms_datasets.process import (
    aggregate,
    apply_filters,
    compute_uptake_metrics,
    load_peptides,
    merge_peptides,
)
from hdxms_datasets.reader import read_csv
from hdxms_datasets.utils import verify_sequence

__all__ = [
    "__version__",
    "HDXDataSet",
    "State",
    "Peptides",
    "ProteinState",
    "ProteinIdentifiers",
    "Structure",
    "Publication",
    "Author",
    "DatasetMetadata",
    "DataBase",
    "RemoteDataBase",
    "load_dataset",
    "submit_dataset",
    "load_peptides",
    "read_csv",
    "merge_peptides",
    "compute_uptake_metrics",
    "apply_filters",
    "aggregate",
    "verify_sequence",
    "identify_format",
]
