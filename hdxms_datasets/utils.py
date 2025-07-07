from __future__ import annotations
import difflib
import narwhals as nw
from narwhals.typing import IntoFrame
from typing import TYPE_CHECKING, cast

import numpy as np

if TYPE_CHECKING:
    from hdxms_datasets.datasets import ProteinInfo


def diff_sequence(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def reconstruct_sequence(peptides: nw.DataFrame, known_sequence: str, n_term: int = 1) -> str:
    """
    Reconstruct the sequence form a dataframe of peptides with sequence information.
    The sequence is reconstructed by replacing the known sequence with the peptide
    sequences at the specified start and end positions.

    Args:
        peptides: DataFrame containing peptide information.
        known_sequence: Starting sequence. Can be a string 'X' as placeholder.
        n_term: The residue number of the N-terminal residue. This is typically 1, can be
            negative in case of purification tags.

    Returns:
        The reconstructed sequence.
    """

    reconstructed = list(known_sequence)
    for start, end, sequence in peptides.select(["start", "end", "sequence"]).iter_rows():  # type: ignore
        start_idx = start - n_term
        assert end - start + 1 == len(sequence), (
            f"Length mismatch at {start}:{end} with sequence {sequence}"
        )

        for i, aa in enumerate(sequence, start=start_idx):
            reconstructed[i] = aa

    return "".join(reconstructed)


def check_sequence(
    peptides: nw.DataFrame, known_sequence: str, n_term: int = 1
) -> list[tuple[int, str, str]]:
    """
    Check the sequence of peptides against the given sequence.

    Args:
        peptides: DataFrame containing peptide information.
        sequence: The original sequence to check against.
        n_term: The number of N-terminal residues to consider.

    Returns:
        A tuple containing the fixed sequence and a list of mismatches.
    """

    reconstructed_sequence = reconstruct_sequence(peptides, known_sequence, n_term)

    mismatches = []
    for r_number, (expected, found) in enumerate(
        zip(known_sequence, reconstructed_sequence), start=n_term
    ):
        if expected != found:
            mismatches.append((r_number, expected, found))

    return mismatches


def default_protein_info(peptides: nw.DataFrame) -> ProteinInfo:
    """Generate minimal protein info from a set of peptides"""
    # Start with partially deuterated peptides as they're most likely to be present

    # Find minimum start and maximum end positions
    min_start = peptides["start"].min()
    max_end = peptides["end"].max()

    # Estimate sequence length
    sequence_length = max_end - min_start + 1

    placeholder_sequence = "X" * sequence_length
    sequence = reconstruct_sequence(peptides, placeholder_sequence, n_term=min_start)

    # Create a minimal ProteinInfo
    return {
        "sequence": sequence,  # sequence with "X" gaps
        "n_term": int(min_start),
        "c_term": int(max_end),
    }


@nw.narwhalify
def contiguous_peptides(df: IntoFrame, start="start", end="end") -> list[tuple[int, int]]:
    """
    Given a dataframe with 'start' and 'end' columns, each describing a range,
    (inclusive intervals), this function returns a list of tuples
    representing contiguous regions.
    """
    # cast to ensure df is a narwhals DataFrame
    df = cast(nw.DataFrame, df).select([start, end]).unique().sort(by=[start, end])

    regions = []
    current_start, current_end = None, 0

    for start_val, end_val in df.select([nw.col(start), nw.col(end)]).iter_rows(named=False):
        if current_start is None:
            # Initialize the first region
            current_start, current_end = start_val, end_val
        elif start_val <= current_end + 1:  # Check for contiguity
            # Extend the current region
            current_end = max(current_end, end_val)
        else:
            # Save the previous region and start a new one
            regions.append((current_start, current_end))
            current_start, current_end = start_val, end_val

    # Don't forget to add the last region
    if current_start is not None:
        regions.append((current_start, current_end))

    return regions


@nw.narwhalify
def non_overlapping_peptides(
    df: IntoFrame,
    start: str = "start",
    end: str = "end",
) -> list[tuple[int, int]]:
    """
    Given a dataframe with 'start' and 'end' columns, each describing a range,
    (inclusive intervals), this function returns a list of tuples
    representing non-overlapping peptides.
    """
    df = cast(nw.DataFrame, df).select([start, end]).unique().sort(by=[start, end])

    regions = df.rows()
    out = [regions[0]]
    for start_val, end_val in regions[1:]:
        if start_val > out[-1][1]:
            out.append((start_val, end_val))
        else:
            continue

    return out


@nw.narwhalify
def peptide_redundancy(
    df: IntoFrame, start: str = "start", end: str = "end"
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the redundancy of peptides in a DataFrame based on their start and end positions.
    Redundancy is defined as the number of peptides overlapping at each position.

    Args:
        df: DataFrame containing peptide information with 'start' and 'end' columns.
        start: Column name for the start position.
        end: Column name for the end position.

    Returns:
        A tuple containing:
        - r_number: An array of positions from the minimum start to the maximum end.
        - redundancy: An array of redundancy counts for each position in r_number.

    """
    df = cast(nw.DataFrame, df).select([start, end]).unique().sort(by=[start, end])
    vmin, vmax = df[start][0], df[end][-1]

    r_number = np.arange(vmin, vmax + 1, dtype=int)
    redundancy = np.zeros_like(r_number, dtype=int)
    for s, e in df.rows():
        i0, i1 = np.searchsorted(r_number, (s, e))
        redundancy[i0:i1] += 1

    return r_number, redundancy
