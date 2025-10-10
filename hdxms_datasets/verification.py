from __future__ import annotations
from hdxms_datasets.models import HDXDataSet, Peptides, Structure
from hdxms_datasets.utils import reconstruct_sequence, verify_sequence
from typing import TYPE_CHECKING, Literal, TypedDict, overload

if TYPE_CHECKING:
    import polars as pl


def verify_dataset(dataset: HDXDataSet):
    """Verify the integrity of the dataset by checking sequences and data files."""
    verify_peptides(dataset)
    if not datafiles_exist(dataset):
        raise ValueError("Missing datafiles")

    if dataset.file_hash is None:
        raise ValueError("Dataset file hash is not set")


def verify_peptides(dataset: HDXDataSet):
    """Verify that all peptide sequences match the protein sequence in the dataset states."""
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


def residue_df_from_structure(structure: Structure) -> pl.DataFrame:
    """Create a dataframe from the structure with chain, resi, resn_TLA"""
    if structure.format not in ["cif", "mmcif"]:
        raise ValueError(f"Unsupported structure format: {structure.format}")

    # create the reference structure amino acid dataframe
    from Bio.PDB.MMCIF2Dict import MMCIF2Dict
    from Bio.Data import IUPACData
    import polars as pl

    mm = MMCIF2Dict(structure.data_file)

    one_to_three = IUPACData.protein_letters_1to3
    AA_codes = [a.upper() for a in list(one_to_three.values())]

    # create a dataframe with chain, resi, resn_TLA from structure
    chain_name = "label_asym_id" if not structure.auth_chain_labels else "auth_asym_id"
    resn_name = "label_seq_id" if not structure.auth_residue_numbers else "auth_seq_id"

    structure_df = (
        pl.DataFrame(
            {
                "chain": mm["_atom_site." + chain_name],
                "resi": mm["_atom_site." + resn_name],
                "resn_TLA": [s.upper() for s in mm["_atom_site.label_comp_id"]],
            }
        )
        .unique()
        .filter(pl.col("resn_TLA").is_in(AA_codes))
    )

    return structure_df


def residue_df_from_peptides(peptides: Peptides) -> pl.DataFrame:
    """Create a dataframe from the peptides with resi, resn_TLA"""
    from Bio.Data import IUPACData
    import polars as pl

    one_to_three = IUPACData.protein_letters_1to3

    peptide_df = peptides.load().to_native()

    start, end = peptide_df["start"].min(), peptide_df["end"].max()
    residues = range(start, end + 1)
    known_sequence = "X" * len(residues)
    sequence = reconstruct_sequence(peptide_df, known_sequence, n_term=start)

    residue_df = (
        pl.DataFrame({"resi": residues, "resn": list(sequence)})
        .filter(pl.col("resn") != "X")
        .with_columns(
            [
                pl.col("resi").cast(str),
                pl.col("resn").replace_strict(one_to_three).str.to_uppercase().alias("resn_TLA"),
            ]
        )
    )

    return residue_df


def build_structure_peptides_comparison(
    structure: Structure,
    peptides: Peptides,
) -> pl.DataFrame:
    """
    Compares residue numbering and identity between a structure and peptides.

    Returns:  dictionary with:
        - total_residues: Total number of residues in the peptides (considering chains)
        - matched_residues: Number of residues that are matched to the structure (by chain and resi)
        - identical_residues: Number of matched residues that have the correct amino acid identity

    """
    structure_df = residue_df_from_structure(structure)
    residue_df = residue_df_from_peptides(peptides)

    chains = (
        peptides.chain if peptides.chain is not None else structure_df["chain"].unique().to_list()
    )

    # supplement the residue_df with all chains
    # multie-chain peptides are expected to correspond to homomultimers
    import polars as pl

    residue_df_chain = pl.concat(
        [residue_df.with_columns(pl.lit(ch).alias("chain")) for ch in chains]
    )

    merged = residue_df_chain.join(
        structure_df,
        on=["chain", "resi"],
        how="left",
    )

    return merged


class CompareSummary(TypedDict):
    total_residues: int
    matched_residues: int
    identical_residues: int


def summarize_compare_table(df: pl.DataFrame) -> CompareSummary:
    """Derive the metrics from the merged table."""
    # rows with a structure match (adjust column names to your schema)
    import polars as pl

    matched = df.drop_nulls(subset=["resn_TLA_right"])
    identical = matched.filter(pl.col("resn_TLA") == pl.col("resn_TLA_right"))

    return {
        "total_residues": df.height,
        "matched_residues": matched.height,
        "identical_residues": identical.height,
    }


@overload
def compare_structure_peptides(
    structure: Structure,
    peptides: Peptides,
    returns: Literal["dict"] = "dict",
) -> CompareSummary: ...


@overload
def compare_structure_peptides(
    structure: Structure,
    peptides: Peptides,
    returns: Literal["df"],
) -> pl.DataFrame: ...


@overload
def compare_structure_peptides(
    structure: Structure,
    peptides: Peptides,
    returns: Literal["both"],
) -> tuple[CompareSummary, pl.DataFrame]: ...


def compare_structure_peptides(
    structure: Structure,
    peptides: Peptides,
    returns: Literal["dict", "df", "both"] = "dict",
) -> pl.DataFrame | CompareSummary | tuple[CompareSummary, pl.DataFrame]:
    """Compares structure and peptide data."""

    df = build_structure_peptides_comparison(structure, peptides)

    if returns == "dict":
        return summarize_compare_table(df)
    elif returns == "df":
        return df
    elif returns == "both":
        return summarize_compare_table(df), df
    else:
        raise ValueError(f"Invalid returns value: {returns!r}")
