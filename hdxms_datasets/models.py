# %%
from __future__ import annotations
import hashlib

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    PlainSerializer,
    AfterValidator,
    ValidationInfo,
    model_validator,
)
from typing import Any, Iterable, List, Optional, Annotated, Type, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from pathlib import Path
import narwhals as nw
from hdxms_datasets import __version__
from hdxms_datasets.formats import FormatSpec

if TYPE_CHECKING:
    from Bio.PDB.Structure import Structure as BioStructure

# %%

ValueType = str | float | int


def extract_values_by_types(obj: Any, target_types: Type | tuple[Type, ...]) -> list[Any]:
    """
    Recursively extract all values of specified type(s) from a nested structure.
    This function can handle Pydantic models, lists, tuples, sets, and dictionaries.

    Args:
        obj: Pydantic model instance or any nested structure
        target_types: Single type or tuple of types to search for

    Returns:
        List of all values matching any of the target types
    """
    values = []

    # Normalize target_types to tuple
    if not isinstance(target_types, tuple):
        target_types = (target_types,)

    # Check if current object is of any target type
    if isinstance(obj, target_types):
        values.append(obj)

    elif isinstance(obj, BaseModel):
        # Iterate through all field values in the Pydantic model
        for field_name, field_value in obj.__dict__.items():
            values.extend(extract_values_by_types(field_value, target_types))

    elif isinstance(obj, (list, tuple, set)):
        # Handle sequences
        for item in obj:
            values.extend(extract_values_by_types(item, target_types))

    elif isinstance(obj, dict):
        # Handle dictionaries (both keys and values)
        for key, value in obj.items():
            values.extend(extract_values_by_types(key, target_types))
            values.extend(extract_values_by_types(value, target_types))

    return values


def validate_datafile_path(x: Path, info: ValidationInfo):
    """Pydantic validator to resolve relative paths based on context"""
    context = info.context
    if context and "dataset_root" in context and not x.is_absolute():
        root = Path(context["dataset_root"])
        x = root / x
    return x


def serialize_datafile_path(x: Path, info: ValidationInfo) -> str:
    """Pydantic serializer to convert paths to relative paths based on context"""
    context = info.context
    if context and "dataset_root" in context:
        relpath = x.relative_to(Path(context["dataset_root"]))
        return relpath.as_posix()
    return x.as_posix()


def serialize_nonfinite_numbers_recursive(obj: Any, info: ValidationInfo):
    import math

    # floats -> sentinel strings
    if isinstance(obj, float):
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        if math.isnan(obj):
            return "NaN"
        return obj

    # Pydantic model -> dict
    if isinstance(obj, BaseModel):
        return serialize_nonfinite_numbers_recursive(obj.__dict__, info)

    # containers
    if isinstance(obj, dict):
        return {k: serialize_nonfinite_numbers_recursive(v, info) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_nonfinite_numbers_recursive(v, info) for v in obj]

    return obj


def validate_nonfinite_numbers_recursive(x: Any, info: ValidationInfo):
    # sentinel strings -> floats; recursive for containers
    if isinstance(x, str):
        if x == "Infinity":
            return float("inf")
        if x == "-Infinity":
            return float("-inf")
        if x == "NaN":
            return float("nan")
        return x

    if isinstance(x, dict):
        return {k: validate_nonfinite_numbers_recursive(v, info) for k, v in x.items()}
    if isinstance(x, list):
        return [validate_nonfinite_numbers_recursive(v, info) for v in x]

    return x


TEXT_FILE_FORMATS = [".csv", ".txt", ".yaml", ".yml", ".json", ".pdb", ".cif"]


def hash_files(data_files: Iterable[Path]) -> str:
    """Compute a hash of all data files in the dataset"""
    hash_obj = hashlib.sha256()
    files = sorted(data_files, key=lambda p: p.as_posix())  # Sort to ensure consistent order
    for f in files:
        if f.suffix in TEXT_FILE_FORMATS:
            content = f.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
            hash_obj.update(content.encode("utf-8"))
        else:
            hash_obj.update(f.read_bytes())

    return hash_obj.hexdigest()


DataFilePath = Annotated[
    Path,
    Field(..., description="Source data file path"),
    AfterValidator(validate_datafile_path),
    PlainSerializer(serialize_datafile_path),
]


class PeptideFormat(str, Enum):
    """Format of the peptide data"""

    DynamX_v3_state = "DynamX_v3_state"
    DynamX_v3_cluster = "DynamX_v3_cluster"
    DynamX_vx_state = "DynamX_vx_state"
    HDExaminer_all_results = "HDExaminer_all_results"
    HDExaminer_all_results_with_units = "HDExaminer_all_results_with_units"
    HDExaminer_peptide_pool = "HDExaminer_peptide_pool"
    HDExaminer_uptake_summary = "HDExaminer_uptake_summary"
    HXMS = "HXMS"
    OpenHDX = "OpenHDX"

    def get_format(self) -> type[FormatSpec]:
        """Get the FormatSpec for this format"""
        from hdxms_datasets.formats import FMT_REGISTRY

        fmt = FMT_REGISTRY.get(self.value)
        if fmt is None:
            raise ValueError(f"FormatSpec not found for format: {self.value}")
        return fmt

    @classmethod
    def identify(cls, path: Path) -> PeptideFormat | None:
        """Identify format from DataFrame"""
        from hdxms_datasets.formats import identify_format

        fmt = identify_format(path)
        if fmt:
            return cls(fmt.__name__)
        return None


class DeuterationType(str, Enum):
    """Experimental Deuteration Type of the peptide"""

    partially_deuterated = "partially_deuterated"
    fully_deuterated = "fully_deuterated"
    non_deuterated = "non_deuterated"


class StructureMapping(BaseModel):
    """Maps peptide HDX-MS data to a structure

    Residue numbers can be mapped from HDX-MS data to a structure using either an residue number
    offset or a specific dictionary mapping.

    """

    entity_id: Annotated[Optional[str], Field(None, description="Entity identifier")] = None
    chain: Annotated[Optional[list[str]], Field(None, description="Chain identifiers")] = None
    residue_offset: Annotated[int, Field(None, description="Residue number offset to apply")] = 0
    mapping: dict[int, int] = Field(default_factory=dict, description="Residue number mapping")

    auth_residue_numbers: Annotated[
        bool, Field(default=False, description="Use author residue numbers")
    ] = False
    auth_chain_labels: Annotated[
        bool, Field(default=False, description="Use author chain labels")
    ] = False

    def map(self, residue_number: int) -> int:
        """Map a residue number using the mapping dictionary and offset"""
        if self.residue_offset:
            return residue_number + self.residue_offset
        elif self.mapping:
            return self.mapping.get(residue_number, residue_number)
        else:
            return residue_number


class Peptides(BaseModel):
    """Information about HDX-MS peptides"""

    data_file: DataFilePath
    data_format: Annotated[PeptideFormat, Field(description="Data format (e.g., OpenHDX)")]
    deuteration_type: Annotated[
        DeuterationType, Field(description="Type of the peptide (e.g., fully_deuterated)")
    ]
    filters: Annotated[
        dict[str, ValueType | list[ValueType]],
        Field(default_factory=dict, description="Filters applied to the data"),
        AfterValidator(validate_nonfinite_numbers_recursive),
        PlainSerializer(serialize_nonfinite_numbers_recursive),
    ]
    pH: Annotated[
        Optional[float], Field(description="pH (read, uncorrected) of the experiment")
    ] = None
    temperature: Annotated[Optional[float], Field(description="Temperature in Kelvin")] = None
    d_percentage: Annotated[Optional[float], Field(description="Deuteration percentage")] = None
    ionic_strength: Annotated[Optional[float], Field(description="Ionic strength in Molar")] = None

    structure_mapping: Annotated[
        StructureMapping, Field(description="Structure mapping information")
    ] = StructureMapping()

    def load(
        self,
        convert: bool = True,
        aggregate: bool | None = None,
        sort_rows: bool = True,
        sort_columns: bool = True,
        drop_null: bool = True,
    ) -> nw.DataFrame:
        """Load the peptides from the data file

        Args:
            convert: Whether to convert the data to a standard format.
            aggregate: Whether to aggregate the data. If None, will aggregate if the data is not already aggregated.
            sort_rows: Whether to sort the rows.
            sort_columns: Whether to sort the columns in a standard order.
            drop_null: Whether to drop columns that are entirely null.

        """
        if self.data_file.exists():
            from hdxms_datasets.process import load_peptides

            return load_peptides(
                self,
                convert=convert,
                aggregate=aggregate,
                sort_rows=sort_rows,
                sort_columns=sort_columns,
                drop_null=drop_null,
            )
        else:
            raise FileNotFoundError(f"Data file {self.data_file} does not exist.")


class ProteinIdentifiers(BaseModel):
    """General protein information"""

    uniprot_accession_number: Annotated[Optional[str], Field(None, description="UniProt ID")] = None
    uniprot_entry_name: Annotated[Optional[str], Field(None, description="UniProt entry name")] = (
        None
    )
    protein_name: Annotated[Optional[str], Field(None, description="Recommended protein name")] = (
        None
    )


class ProteinState(BaseModel):
    """Protein information for a specific state"""

    sequence: Annotated[str | list[str], Field(description="Amino acid sequence")]
    n_term: Annotated[int, Field(description="N-terminal residue number")]
    c_term: Annotated[int, Field(description="C-terminal residue number")]
    mutations: Annotated[Optional[list[str]], Field(description="List of mutations")] = None
    oligomeric_state: Annotated[Optional[int], Field(description="Oligomeric state")] = None
    ligand: Annotated[Optional[str], Field(description="Bound ligand information")] = None

    @model_validator(mode="after")
    def check_sequence(self):
        if len(self.sequence) != self.c_term - self.n_term + 1:
            raise ValueError(
                f"Sequence length does not match N-term and C-term residue numbers, found: {len(self.sequence)}, expected: {self.c_term - self.n_term + 1}"
            )
        return self


class State(BaseModel):
    """Information about HDX-MS state"""

    name: Annotated[str, Field(description="State name")]
    peptides: list[Peptides] = Field(..., description="List of peptides in this state")
    description: Annotated[str, Field(description="State description")] = ""  # TODO max length?
    protein_state: ProteinState = Field(..., description="Protein information for this state")


def residue_number_mapping(
    cif_path: Path, chain=True, residue=True
) -> dict[tuple[str, str], tuple[str, str]]:
    """Create a mapping from author residue numbers to RCSB residue numbers from an mmCIF file.

    Args:
        cif_path: Path to the mmCIF file.
        chain: Whether to include chain mapping.
        residue: Whether to include residue number mapping.


    """
    try:
        from Bio.PDB.MMCIF2Dict import MMCIF2Dict
    except ImportError:
        raise ImportError("Biopython is required for residue number mapping from mmCIF files.")

    mm = MMCIF2Dict(cif_path)

    label_asym = mm["_atom_site.label_asym_id"]
    if chain:
        auth_asym = mm.get("_atom_site.auth_asym_id", label_asym)
    else:
        auth_asym = label_asym

    label_seq = mm.get("_atom_site.label_seq_id", [])
    if residue:
        auth_seq = mm.get("_atom_site.auth_seq_id", label_seq)
    else:
        auth_seq = label_seq

    # maps author chain/residue numbers to PDB chain/residue numbers
    mapping = {
        (a_asym, a_seq): (l_asym, l_seq)
        for l_asym, l_seq, a_asym, a_seq in zip(label_asym, label_seq, auth_asym, auth_seq)
        if l_asym != a_asym or l_seq != a_seq  # dont include identical mappings
    }

    return mapping


class Structure(BaseModel):
    """Structural model file information

    Residues or protein chains may have different numbering/labels depending on if they are
    the assigned labels by the author of the structure ('auth') or renumbered by the RCSB PDB.

    If your HDX data uses the author numbering/labels, set `auth_residue_numbers` and/or
    `auth_chain_labels` to True.
    """

    data_file: DataFilePath
    format: Annotated[str, Field(description="Format of the structure file (e.g., PDB, mmCIF)")]
    description: Annotated[Optional[str], Field(description="Description of the structure")] = None

    # source database identifiers
    pdb_id: Annotated[Optional[str], Field(None, description="RCSB PDB ID")] = None
    alphafold_id: Annotated[Optional[str], Field(None, description="AlphaFold ID")] = None

    def pdbemolstar_custom_data(self) -> dict[str, Any]:
        """
        Returns a dictionary with custom data for PDBeMolstar visualization.
        """

        if self.format in ["bcif"]:
            binary = True
        else:
            binary = False

        if self.data_file.is_file():
            data = self.data_file.read_bytes()
        else:
            raise ValueError(f"Path {self.data_file} is not a file.")

        return {
            "data": data,
            "format": self.format,
            "binary": binary,
        }

    def get_auth_residue_mapping(self) -> dict[tuple[str, str], tuple[str, str]]:
        """Create a mapping from author residue numbers to RCSB residue numbers."""

        if self.label_auth_mapping is not None:
            return self.label_auth_mapping

        else:
            if self.format.lower() not in ["cif", "mmcif"]:
                raise ValueError("Author residue number mapping is only supported for mmCIF files.")

            mapping = residue_number_mapping(self.data_file)
            self.label_auth_mapping = mapping
            return mapping

    def to_biopython(self) -> BioStructure:
        """Load the structure using Biopython"""
        try:
            from Bio.PDB.PDBParser import PDBParser
            from Bio.PDB.MMCIFParser import MMCIFParser
        except ImportError:
            raise ImportError("Biopython is required to load structures.")

        if self.format.lower() in ["pdb"]:
            parser = PDBParser(QUIET=True)
        elif self.format.lower() in ["cif", "mmcif"]:
            parser = MMCIFParser(QUIET=True)
        else:
            raise ValueError(f"Unsupported structure format: {self.format}")

        structure = parser.get_structure(self.pdb_id or "structure", self.data_file)
        assert structure is not None

        return structure


class Publication(BaseModel):
    """Publication information"""

    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None


class DataRepository(BaseModel):
    """Information about the data repository where the source data is published"""

    name: Annotated[str, Field(..., description="Repository name")]  # ie Pride, Zenodo,
    url: Annotated[Optional[HttpUrl], Field(None, description="Repository URL")]
    identifier: Annotated[Optional[str], Field(None, description="Repository entry identifier")]
    doi: Annotated[Optional[str], Field(None, description="Repository DOI")]
    description: Annotated[Optional[str], Field(None, description="Repository description")]


class Author(BaseModel):
    name: Annotated[str, Field(..., description="Author name")]
    orcid: Annotated[Optional[str], Field(None, description="Author ORCID ID")] = None
    affiliation: Annotated[Optional[str], Field(None, description="Author affiliation")] = None
    contact_email: Annotated[Optional[str], Field(description="Contact email")] = None

    @property
    def last_name(self) -> str:
        # Lastname, Firstname
        if ", " in self.name:
            return self.name.split(", ")[0]
        # Firstname Lastname
        else:
            return self.name.split(" ")[-1]


class DatasetMetadata(BaseModel):
    # Authors, publication, license
    authors: Annotated[list[Author], Field(..., description="Dataset authors")]
    license: Annotated[str, Field(description="License for the dataset")]

    publication: Annotated[Optional[Publication], Field(description="Associated publication")] = (
        None
    )
    repository: Annotated[Optional[DataRepository], Field(description="Data repository")] = None

    # Technical information
    created_date: Annotated[
        datetime, Field(default_factory=datetime.now, description="Creation date")
    ]
    modified_date: Annotated[
        datetime, Field(default_factory=datetime.now, description="Last modified date")
    ]
    package_version: Annotated[
        str,
        Field(
            default=__version__,
            description="hdxms-datasets package version used to create this dataset",
        ),
    ]
    dataset_version: Annotated[
        int, Field(default=1, description="Version of this specific dataset")
    ]

    # Source information
    conversion_notes: Annotated[
        Optional[str], Field(None, description="Notes about data conversion")
    ] = None

    @model_validator(mode="before")
    def ensure_license_present(cls, values):
        # `values` is the raw input mapping; raise a ValueError with a custom message
        if isinstance(values, dict):
            lic = values.get("license")
            if lic is None or (isinstance(lic, str) and not lic.strip()):
                raise ValueError(
                    "Missing required field 'license': please provide a license; we recommend using 'CC0' or 'CC BY 4.0'."
                )
        return values


def id_factory() -> str:
    """Factory function to generate a new dataset ID"""
    from hdxms_datasets.database import mint_new_dataset_id

    return mint_new_dataset_id()


class HDXDataSet(BaseModel):
    """HDX-MS dataset containing multiple states"""

    hdx_id: Annotated[
        str, Field(default_factory=id_factory, description="HDX-MS dataset identifier")
    ]

    # Basic information
    description: Annotated[Optional[str], Field(None, description="Dataset description")]

    states: list[State] = Field(description="List of HDX states in the dataset")
    structure: Annotated[Structure, Field(description="Structural model file path")]
    protein_identifiers: Annotated[
        ProteinIdentifiers, Field(description="Protein identifiers (UniProt, etc.)")
    ]
    metadata: Annotated[DatasetMetadata, Field(description="Dataset metadata")]
    file_hash: Annotated[
        Optional[str], Field(None, init=False, description="Hash of the files in the dataset")
    ]

    @model_validator(mode="after")
    def validate_hdx_id(self):
        """Validate hdx_id format: 'HDX_' followed by 8 uppercase alphanumeric chars (e.g. HDX_3BAE2080)."""
        from hdxms_datasets.database import valid_id

        if not valid_id(self.hdx_id):
            raise ValueError(
                "hdx_id must match pattern 'HDX_XXXXXXXX' where X are uppercase letters or digits, e.g. 'HDX_3BAE2080'"
            )
        return self

    @model_validator(mode="after")
    def compute_file_hash(self):
        """Compute a hash of the dataset based on its data files"""
        if any(not p.exists() for p in self.data_files):
            self.file_hash = None
            return self

        self.file_hash = self.hash_files()[:16]  # Shorten to 16 characters

        return self

    @model_validator(mode="after")
    def verify_unique_state_names(self):
        """Ensure that all state names are unique within the dataset"""
        state_names = [state.name for state in self.states]
        if len(state_names) != len(set(state_names)):
            raise ValueError("State names must be unique within the dataset.")
        return self

    def hash_files(self) -> str:
        return hash_files(self.data_files)  # Ensure files are sorted and hashed consistently

    def validate_file_integrity(self) -> bool:
        """Match hash of files with the stored hash"""
        if self.file_hash is None:
            return False
        current_hash = self.hash_files()
        return current_hash.startswith(self.file_hash)

    def get_state(self, state: str | int) -> State:
        """Get a specific state by name or index"""
        if isinstance(state, int):
            return self.states[state]
        elif isinstance(state, str):
            for s in self.states:
                if s.name == state:
                    return s
        raise ValueError(f"State '{state}' not found in dataset.")

    @property
    def data_files(self) -> list[Path]:
        """List of all data files in the dataset"""
        return sorted(set(extract_values_by_types(self, Path)))

    @classmethod
    def from_json(
        cls,
        json_str: str,
        dataset_root: Optional[Path] = None,
    ) -> HDXDataSet:
        """Load dataset from JSON string

        Args:
            json_str: JSON string representing the dataset
            dataset_root: Optional root directory to resolve relative paths

        Returns:
            HDXDataSet instance.

        """
        if dataset_root is None:
            context = {}
        else:
            context = {"dataset_root": dataset_root}
        return cls.model_validate_json(json_str, context=context)


# %%
