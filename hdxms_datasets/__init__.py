"""Top-level package for HDXMS Datasets."""

from hdxms_datasets.__version__ import __version__

from hdxms_datasets.models import (
    HDXDataSet,
    HDXState,
    Peptides,
    ProteinState,
    ProteinIdentifiers,
    Structure,
    Publication,
    Author,
    DatasetMetadata,
)
from hdxms_datasets.database import DataBase, RemoteDataBase, load_dataset
from hdxms_datasets.loader import load_peptides, read_csv
from hdxms_datasets.process import (
    merge_peptides,
    compute_uptake_metrics,
    apply_filters,
    aggregate,
)


__all__ = [
    "__version__",
    "HDXDataSet",
    "HDXState",
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
    "load_peptides",
    "read_csv",
    "merge_peptides",
    "compute_uptake_metrics",
    "apply_filters",
    "aggregate",
]
