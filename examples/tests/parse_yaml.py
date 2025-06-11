# %%

from dataclasses import dataclass, field
from typing import Any
from hdxms_datasets.formats import FMT_LUT
import hdxms_datasets.process as process
import yaml
from pathlib import Path


# %%

root = Path().resolve().parent.parent
data_dir = root / r"tests\datasets\1704204434_SecB_Krishnamurthy"
fpath = data_dir / "hdx_spec.yaml"

hdx_spec = yaml.safe_load(fpath.read_text(encoding="utf-8"))  # type: ignore


# %%

from hdxms_datasets.datasets import PeptideTableFile, Peptides, StructureFile

data_file_spec = hdx_spec["data_files"]
data_files = {}
for name, spec in data_file_spec.items():
    fpath = Path(data_dir / spec["filename"])

    if spec["type"] == "structure":
        format = spec["format"]
        data_file = StructureFile(
            name=name,
            filepath_or_buffer=fpath,
            format=format,
            extension=fpath.suffix,
        )
        file_class = StructureFile
    elif spec["type"] == "peptide_table":
        format = FMT_LUT.get(spec["format"], None)
        data_file = PeptideTableFile(
            name=name,
            filepath_or_buffer=fpath,
            format=format,
            extension=fpath.suffix,
        )
    else:
        raise ValueError(f"Unknown data file type {spec['type']} for {name}.")

    data_files[name] = data_file

data_files

# %%


@dataclass
class Structure:
    data_file: StructureFile
    chain: list[str] = field(default_factory=list)  # empty list for all chains
    auth_residue_numbers: bool = field(default=False)

    def pdbemolstar_custom_data(self) -> dict[str, Any]:
        """
        Returns a dictionary with custom data for PDBeMolstar visualization.
        """

        return self.data_file.pdbemolstar_custom_data()


# %%

structures = hdx_spec["structures"]
structure_name = "SecB_tetramer"
spec = structures[structure_name]

structure_file = data_files[spec["data_file"]]
structure_file

Structure(
    data_file=structure_file,
    chain=spec.get("chain", []),  # empty list for all chains
    auth_residue_numbers=spec.get("auth_residue_numbers", False),
)

# %%


def parse_structures(
    structures_spec: dict[str, Any], data_files: dict[str, StructureFile]
) -> dict[str, Structure]:
    """
    Parse the structures specification and return a dictionary of Structure objects.

    Args:
        structures_spec: Dictionary containing structure specifications.
        data_files: Dictionary of available data files.

    Returns:
        Dictionary of Structure objects keyed by structure name.
    """
    structures = {}
    for name, spec in structures_spec.items():
        data_file = data_files[spec["data_file"]]
        structure = Structure(
            data_file=data_file,
            chain=spec.get("chain", []),  # empty list for all chains
            auth_residue_numbers=spec.get("auth_residue_numbers", False),
        )
        structures[name] = structure
    return structures


parse_structures(hdx_spec["structures"], data_files)


def parse_peptides(
    peptides_spec: dict[str, Any], data_files: dict[str, PeptideTableFile]
) -> dict[str, dict[str, Peptides]]:
    """
    Parse the peptides specification and return a dictionary of PeptideTableFile objects.

    Args:
        peptides_spec: Dictionary containing peptide specifications.
        data_files: Dictionary of available data files.

    Returns:
        Dictionary of PeptideTableFile objects keyed by peptide name.
    """
    peptides = {}
    for state_name, state_peptides in peptides_spec.items():
        # Build peptide dictionary for this state
        state_peptide_dict = {}

        # Process each peptide set for this state
        for peptide_type, peptide_spec in state_peptides.items():
            peptide_obj = Peptides(
                data_file=data_files[peptide_spec["data_file"]],
                filters=peptide_spec["filters"],
                metadata=peptide_spec.get("metadata", None),
            )

            # Add to state-specific dictionary
            state_peptide_dict[peptide_type] = peptide_obj

        peptides[state_name] = state_peptide_dict

    return peptides


peptides = parse_peptides(hdx_spec["peptides"], data_files)
peptides

# %%


# %%
process.parse_data_files(hdx_spec["data_files"], data_dir)

# %%
