from __future__ import annotations
from collections import defaultdict
import difflib
import narwhals as nw
from narwhals.typing import IntoFrame, DataFrameT
from typing import Any, Optional, cast

import numpy as np

from hdxms_datasets.models import DeuterationType, Peptides


def diff_sequence(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def records_to_dict(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Convert a list of records to a dictionary.
    """
    output = defaultdict(list)
    for record in records:
        for key, value in record.items():
            output[key].append(value)

    return dict(output)


@nw.narwhalify
def reconstruct_sequence(
    peptides: nw.DataFrame,
    known_sequence: str,
    n_term: int = 1,
    start="start",
    end="end",
    sequence="sequence",
) -> str:
    """
    Reconstruct the sequence form a dataframe of peptides with sequence information.
    The sequence is reconstructed by replacing the known sequence with the peptide
    sequences at the specified start and end positions.

    Args:
        peptides: DataFrame containing peptide information.
        known_sequence: Starting sequence. Can be a string 'X' as placeholder.
        n_term: The residue number of the N-terminal residue. This is typically 1, can be
            negative in case of purification tags.
        start: Column name for the start position of the peptide.
        end: Column name for the end position of the peptide.
        sequence: Column name for the peptide sequence.

    Returns:
        The reconstructed sequence.
    """

    reconstructed = list(known_sequence)
    for start_, end_, sequence_ in peptides.select([start, end, sequence]).iter_rows():  # type: ignore
        start_idx = start_ - n_term
        assert end_ - start_ + 1 == len(sequence_), (
            f"Length mismatch at {start_}:{end_} with sequence {sequence_}"
        )

        for i, aa in enumerate(sequence_, start=start_idx):
            reconstructed[i] = aa

    return "".join(reconstructed)


@nw.narwhalify
def verify_sequence(
    peptides: IntoFrame,
    known_sequence: str,
    n_term: int = 1,
    start="start",
    end="end",
    sequence="sequence",
) -> list[tuple[int, str, str]]:
    """
    Verify the sequence of peptides against the given sequence.

    Args:
        peptides: DataFrame containing peptide information.
        sequence: The original sequence to check against.
        n_term: The number of N-terminal residues to consider.

    Returns:
        A tuple containing the fixed sequence and a list of mismatches.
    """

    reconstructed_sequence = reconstruct_sequence(
        peptides, known_sequence, n_term, start=start, end=end, sequence=sequence
    )

    mismatches = []
    for r_number, (expected, found) in enumerate(
        zip(known_sequence, reconstructed_sequence), start=n_term
    ):
        if expected != found:
            mismatches.append((r_number, expected, found))

    return mismatches


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


def get_peptides_by_type(
    peptides: list[Peptides], deuteration_type: DeuterationType
) -> Optional[Peptides]:
    """Get peptides of a specific deuteration type."""
    matching_peptides = [p for p in peptides if p.deuteration_type == deuteration_type]
    if not matching_peptides:
        return None
    if len(matching_peptides) > 1:
        return None
    return matching_peptides[0]


def peptides_are_unique(peptides_df: nw.DataFrame) -> bool:
    """Check if the peptides in the dataframe are unique."""
    unique_peptides = peptides_df.select(["start", "end"]).unique()
    return len(unique_peptides) == len(peptides_df)
