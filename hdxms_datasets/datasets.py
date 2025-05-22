from __future__ import annotations

import shutil
import time
import uuid
import warnings
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from string import Template
from typing import Any, NotRequired, Optional, Type, TypedDict, Union

import narwhals as nw
import yaml

import hdxms_datasets.process as process
from hdxms_datasets.formats import HDXFormat, identify_format
from hdxms_datasets.reader import read_csv
from contextlib import contextmanager

from hdxms_datasets.utils import default_protein_info

TEMPLATE_DIR = Path(__file__).parent / "template"
ValueType = str | float | int


ALLOW_MISSING_PROTEIN_INFO = False


@contextmanager
def allow_missing_protein_info(allow=True):
    """Context manager to temporarily allow missing protein information"""
    global ALLOW_MISSING_PROTEIN_INFO
    old_value = ALLOW_MISSING_PROTEIN_INFO
    ALLOW_MISSING_PROTEIN_INFO = allow
    try:
        yield
    finally:
        ALLOW_MISSING_PROTEIN_INFO = old_value


def create_dataset(
    target_dir: Path,
    author_name: str,
    tag: Optional[str] = None,
    template_dir: Path = TEMPLATE_DIR,
) -> str:
    """
    Create a dataset in the specified target directory.

    Args:
        target_dir: The directory where the dataset will be created.
        author_name: The name of the author of the dataset.
        tag: An optional tag to append to the directory name. Defaults to None.
        template_dir: The directory containing the template files for the dataset. Defaults to TEMPLATE_DIR.

    Returns:
        The id of the created dataset.

    """
    dirname = str(int(time.time()))

    if tag:
        dirname += f"_{tag}"

    dirname += f"_{author_name}"

    target_dir.mkdir(parents=True, exist_ok=True)
    target_dir = target_dir / dirname

    shutil.copytree(template_dir, target_dir)

    (target_dir / "readme.md").write_text(f"# {dirname}")

    return dirname


@dataclass(frozen=True)
class DataFile:
    name: str

    filepath_or_buffer: Union[Path, StringIO]

    format: Optional[HDXFormat] = None

    extension: Optional[str] = None
    """File extension, e.g. .csv, in case of a file-like object"""

    def read(self) -> nw.DataFrame:
        if isinstance(self.filepath_or_buffer, StringIO):
            extension = self.extension
            assert isinstance(extension, str), "File-like object must have an extension"
        else:
            extension = self.filepath_or_buffer.suffix[1:]

        if extension == "csv":
            return read_csv(self.filepath_or_buffer)
        else:
            raise ValueError(f"Invalid file extension {self.extension!r}")


class ProteinInfo(TypedDict):
    """TypedDict for protein information in a state"""

    sequence: str  # Amino acid sequence
    n_term: int  # N-terminal residue number
    c_term: int  # C-terminal residue number
    mutations: NotRequired[list[str]]  # Optional list of mutations
    oligomeric_state: NotRequired[int]  # Optional oligomeric state
    ligand: NotRequired[str]  # Optional bound ligand information
    uniprot_id: NotRequired[str]  # Optional UniProt ID
    molecular_weight: NotRequired[float]  # Optional molecular weight in Da


@dataclass
class Peptides:
    data_file: DataFile
    filters: dict[str, ValueType | list[ValueType]]

    metadata: dict  #

    _cache: dict[tuple[bool, bool, bool, bool], nw.DataFrame] = field(
        init=False, default_factory=dict
    )

    def load(self, convert=True, aggregate=True, sort=True, drop_null=True) -> nw.DataFrame:
        cache_key = (convert, aggregate, sort, drop_null)
        if cache_key in self._cache:
            return self._cache[cache_key]

        df = process.filter_from_spec(self.data_file.read(), **self.filters)

        is_aggregated = getattr(self.data_file.format, "aggregated", False)
        if aggregate and is_aggregated:
            warnings.warn("Data format is pre-aggregated. Aggregation will be skipped.")
            aggregate = False

        if not convert and aggregate:
            warnings.warn("Cannot aggregate data without conversion. Aggeregation will be skipped.")
            aggregate = False

        if not convert and sort:
            warnings.warn("Cannot sort data without conversion. Sorting will be skipped.")
            sort = False

        if convert:
            if self.data_file.format is None:
                print("is none", self.data_file.name)
                format = identify_format(df.columns)
            else:
                format = self.data_file.format

            if format is None:
                raise ValueError("Could not identify format")

            df = format.convert(df)

        if aggregate:
            df = process.aggregate(df)

        if sort:
            df = process.sort(df)

        if drop_null:
            df = process.drop_null_columns(df)

        self._cache[cache_key] = df

        return df

    def get_temperature(self, unit="K") -> Optional[float]:
        """Get the temperature of the experiment"""
        try:
            temperature = self.metadata["temperature"]
            return process.convert_temperature(temperature, unit)
        except KeyError:
            return None

    def get_pH(self) -> Optional[float]:
        """Get the pH of the experiment"""
        try:
            return self.metadata["pH"]
        except KeyError:
            return None


@dataclass
class DataState:
    """Encapsulates all data for a specific protein state"""

    name: str
    """Name of the state"""

    peptides: dict[str, Peptides]
    """Dictionary of peptide sets for this state"""

    protein: ProteinInfo
    """Protein information for this state"""

    def get_peptides(self, peptide_set: str) -> Peptides:
        """Get a specific peptide set"""
        try:
            return self.peptides[peptide_set]
        except KeyError:
            raise KeyError(f"Peptide set '{peptide_set}' not found in state '{self.name}'")

    def get_sequence(self) -> str:
        """Get the protein sequence for this state"""
        return self.protein["sequence"]

    def get_protein_property(self, property_name: str) -> Any:
        """Get a specific protein property"""
        try:
            return self.protein[property_name]
        except KeyError:
            raise KeyError(f"Property '{property_name}' not found in state '{self.name}'")

    def compute_uptake_metrics(self) -> nw.DataFrame:
        """Compute uptake metrics for this state"""
        peptide_types = list(self.peptides.keys())

        if "fully_deuterated" in peptide_types:
            fd = self.peptides["fully_deuterated"].load()
        else:
            fd = None

        if "non_deuterated" in peptide_types:
            nd = self.peptides["non_deuterated"].load()
        else:
            nd = None

        pd = self.peptides["partially_deuterated"].load()

        merged = process.merge_peptides(
            partially_deuterated=pd, fully_deuterated=fd, non_deuterated=nd
        )
        return process.compute_uptake_metrics(merged)


@dataclass
class DataSet:
    data_id: str
    """Unique identifier for the dataset"""

    data_files: dict[str, DataFile]
    """Dictionary of data files"""

    hdx_specification: dict
    """Dictionary with HDX-MS state specification"""

    metadata: dict = field(default_factory=dict)  # author, publication, etc

    states: dict[str, DataState] = field(init=False, default_factory=dict)

    def __post_init__(self):
        # Create state objects
        for state_name, state_peptides in self.hdx_specification["peptides"].items():
            # Build peptide dictionary for this state
            state_peptide_dict = {}

            # Process each peptide set for this state
            for peptide_type, peptide_spec in state_peptides.items():
                peptide_obj = Peptides(
                    data_file=self.data_files[peptide_spec["data_file"]],
                    filters=peptide_spec["filters"],
                    metadata=peptide_spec.get("metadata", {}),
                )

                # Add to state-specific dictionary
                state_peptide_dict[peptide_type] = peptide_obj

            # Get protein information for this state
            try:
                protein_info = self.protein_spec[state_name]
            except KeyError:
                # take partially deuterated peptides as default,
                # if not available, take the first one
                peptide_df = state_peptide_dict.get(
                    "partially_deuterated", next(iter(state_peptide_dict.values()))
                ).load()

                if ALLOW_MISSING_PROTEIN_INFO:
                    # Generate minimal protein info from peptides
                    protein_info = default_protein_info(peptide_df)
                    warnings.warn(
                        f"Generated minimal protein info for state '{state_name}'. "
                        f"This is not recommended for production use."
                    )
                else:
                    raise KeyError(
                        f"No protein information found for state '{state_name}'. "
                        f"Use 'allow_missing_protein_info()' context manager to generate minimal info."
                    )

            # Create and store the DataState object
            self.states[state_name] = DataState(
                name=state_name, peptides=state_peptide_dict, protein=protein_info
            )

    def get_state(self, state: str | int) -> DataState:
        """
        Get a specific state by name or index
        """
        if isinstance(state, int):
            return self.states[list(self.states.keys())[state]]
        elif isinstance(state, str):
            return self.states[state]
        else:
            raise TypeError(f"Invalid type {type(state)} for state {state!r}")

    @classmethod
    def from_spec(
        cls,
        hdx_spec: dict,
        data_dir: Path,
        data_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        data_id = data_id or uuid.uuid4().hex
        data_files = process.parse_data_files(hdx_spec["data_files"], data_dir)
        return cls(
            data_id=data_id,
            data_files=data_files,
            hdx_specification=hdx_spec,
            metadata=metadata or {},
        )

    @property
    def protein_spec(self) -> dict[str, ProteinInfo]:
        """Access the protein section of the specification"""
        return self.hdx_specification.get("protein", {})

    @property
    def peptide_spec(self) -> dict:
        return self.hdx_specification["peptides"]

    @property
    def peptides_per_state(self) -> dict[str, list[str]]:
        """Dictionary of state names and list of peptide sets for each state"""
        return {state: list(spec) for state, spec in self.peptide_spec.items()}

    def describe(
        self,
        peptide_template: Optional[str] = "Total peptides: $num_peptides, timepoints: $timepoints",
        return_type: Union[Type[str], type[dict]] = str,
    ) -> Union[dict, str]:
        def fmt_t(val: str | float | int) -> str:
            if isinstance(val, str):
                return val
            elif isinstance(val, (int, float)):
                return f"{val:.1f}"
            else:
                raise TypeError(f"Invalid type {type(val)} for value {val!r}")

        output_dict = {}
        for state in self.states.values():
            state_desc = {}
            if peptide_template:
                for peptides_types, peptides in state.peptides.items():
                    peptide_df = peptides.load()
                    timepoints = peptide_df["exposure"].unique()
                    mapping = {
                        "num_peptides": len(peptide_df),
                        "num_timepoints": len(timepoints),
                        "timepoints": ", ".join([fmt_t(t) for t in timepoints]),
                    }
                    mapping["timepoints"]
                    state_desc[peptides_types] = Template(peptide_template).substitute(**mapping)

            output_dict[state.name] = state_desc

        if return_type is str:
            return yaml.dump(output_dict, sort_keys=False)
        elif return_type is dict:
            return output_dict
        else:
            raise TypeError(f"Invalid return type {return_type!r}")

    def cite(self) -> str:
        """
        Returns citation information
        """

        raise NotImplementedError("Citation information is not yet implemented")
        try:
            return self.metadata["publications"]
        except KeyError:
            return "No publication information available"

    def __len__(self) -> int:
        return len(self.states)
