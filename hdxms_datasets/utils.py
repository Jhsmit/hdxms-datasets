import difflib
import narwhals as nw


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
    for start, end, sequence in peptides["start", "end", "sequence"].iter_rows():
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
