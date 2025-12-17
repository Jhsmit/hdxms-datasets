from __future__ import annotations
from hdxms_datasets.models import HDXDataSet, Peptides, Structure, StructureMapping
from hdxms_datasets.utils import reconstruct_sequence, verify_sequence
from typing import TYPE_CHECKING, Literal, TypedDict, overload
from packaging.version import Version

if TYPE_CHECKING:
    import polars as pl


def verify_dataset(dataset: HDXDataSet, strict: bool = True):
    """Verify the integrity of the dataset by checking sequences and data files."""
    verify_peptides(dataset)
    if not datafiles_exist(dataset):
        raise ValueError("Missing datafiles")

    if dataset.file_hash is None:
        raise ValueError("Dataset file hash is not set")

    if strict:
        verify_version(dataset)


def verify_version(dataset: HDXDataSet):
    """Verify that the dataset was created with a pep 440 compliant version."""
    ver_str = dataset.metadata.package_version

    v = Version(ver_str)  # type: ignore

    if v.pre:
        raise ValueError(
            f"A pre-release version of `hdxms-datasets` was used to create this dataset: {ver_str}"
        )
    if v.dev:
        raise ValueError(
            f"A development version of `hdxms-datasets` was used to create this dataset: {ver_str}"
        )
    if v.local:
        raise ValueError(
            f"A local version of `hdxms-datasets` was used to create this dataset: {ver_str}"
        )


def verify_peptides(dataset: HDXDataSet):
    """Verify that all peptide sequences match the protein sequence in the dataset states."""
    for state in dataset.states:
        sequence = state.protein_state.sequence
        for i, peptides in enumerate(state.peptides):
            try:
                peptide_table = peptides.load()
            except Exception as e:
                raise ValueError(f"State: {state.name}, Peptides[{i}] failed to load: {e}")
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


def residue_df_from_structure(
    structure: Structure, mapping: StructureMapping = StructureMapping()
) -> pl.DataFrame:
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
    chain_name = "label_asym_id" if not mapping.auth_chain_labels else "auth_asym_id"
    resn_name = "label_seq_id" if not mapping.auth_residue_numbers else "auth_seq_id"

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
    """Create a dataframe from the peptides with resi, resn_TLA.

    Args:
        peptides: Peptides object

    Returns:
        DataFrame with columns:
            resi: residue number (int)
            resn: one letter amino acid code (str)
            resn_TLA: three letter amino acid code (str)


    """
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
                pl.col("resi"),
                pl.col("resn").replace_strict(one_to_three).str.to_uppercase().alias("resn_TLA"),
            ]
        )
    )

    return residue_df


def residue_df_from_sequence(
    sequence: str,
    n_term: int = 1,
) -> pl.DataFrame:
    from Bio.Data import IUPACData
    import polars as pl

    one_to_three = IUPACData.protein_letters_1to3

    residue_df = (
        pl.DataFrame({"resn": list(sequence)})
        .with_columns(
            [pl.col("resn").replace_strict(one_to_three).str.to_uppercase().alias("resn_TLA")]
        )
        .with_row_index(offset=n_term, name="resi")
    )
    return residue_df


def build_structure_peptides_comparison(
    structure: Structure,
    peptides: Peptides,
) -> pl.DataFrame:
    """
    Compares residue numbering and identity between a structure and peptides.

    Applies any residue offset defined in the peptides' structure mapping.

    Returns:
        A DataFrame merging structure and peptide residue information.
    """
    structure_df = residue_df_from_structure(structure, peptides.structure_mapping)
    residue_df = residue_df_from_peptides(peptides)

    import polars as pl

    # apply residue offset to peptides
    # doesnt support 'mapping' dicts yet
    if peptides.structure_mapping.mapping:
        raise NotImplementedError("Custom residue mapping is not supported yet.")

    residue_df = residue_df.with_columns(
        (pl.col("resi") + peptides.structure_mapping.residue_offset).cast(str).alias("resi")
    )

    chains = (
        peptides.structure_mapping.chain
        if peptides.structure_mapping.chain is not None
        else structure_df["chain"].unique().to_list()
    )

    # supplement the residue_df with all chains
    # multi-chain peptides are expected to correspond to homomultimers
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
    """Compares structure and peptide data.

    Returned dataframe has the following columns:
    resi (str): Residue number from peptides
    resn: (str): One letter amino acid code from peptides
    resn_TLA: (str): Three letter amino acid code from peptides
    chain (str): Chain identifier
    resn_TLA_right: (str): Three letter amino acid code from structure (null if no match)

    """

    df = build_structure_peptides_comparison(structure, peptides)

    if returns == "dict":
        return summarize_compare_table(df)
    elif returns == "df":
        return df
    elif returns == "both":
        return summarize_compare_table(df), df
    else:
        raise ValueError(f"Invalid returns value: {returns!r}")


def residue_offset_optimization(
    structure: Structure,
    peptides: Peptides,
    search_range: tuple[int, int] = (-100, 100),
) -> int:
    """
    Optimize residue offset to maximize matched residues between structure and peptides.
    Ignores current offset on the peptides' structure mapping.

    Args:
        structure: Structure object
        peptides: Peptides object
        search_range: Tuple of (min_offset, max_offset) to search

    Returns:
        The optimal residue offset as an integer.
    """

    import polars as pl

    structure_df = residue_df_from_structure(structure, peptides.structure_mapping)
    residue_df = residue_df_from_peptides(peptides)
    residue_df = pl.concat(
        [
            residue_df.with_columns(pl.lit(ch).alias("chain"))
            for ch in peptides.structure_mapping.chain or []
        ]
    )

    best_offset = search_range[0]
    prev_result = -float("inf")
    for offset in range(*search_range):
        residue_df_with_offset = residue_df.with_columns(
            (pl.col("resi").cast(int) + offset).cast(str).alias("resi")
        )

        merged = residue_df_with_offset.join(
            structure_df,
            on=["chain", "resi"],
            how="left",
        )

        matched = merged.drop_nulls(subset=["resn_TLA_right"]).filter(
            pl.col("resn_TLA") == pl.col("resn_TLA_right")
        )

        result = matched.height
        if result > prev_result:
            best_offset = offset
            prev_result = result

    return best_offset
