from pathlib import Path
import pytest
from hdxms_datasets.datavault import DataVault
from hdxms_datasets.utils import check_sequence
import polars as pl
import numpy as np
import narwhals as nw

TEST_PTH = Path(__file__).parent
DATA_ID = "1704204434_SecB_Krishnamurthy"


peptide_intervals_indices = [
    (0, 8),
    (5, 12),
    (16, 21),
    (19, 25),
    (26, 28),
]

peptide_data_sequence = "SIAGIEGTQMAHCLGAYCPNILFPAAREGAMCP"
known_sequence = "SIAGIEGTTMAHCLGAYCPNILFGAAREGAMCP"

r_number_default = np.arange(1, len(peptide_data_sequence) + 1)
r_number_tag = r_number_default - 5

expected_mismatches_by_inx = [(8, "T", "Q"), (23, "G", "P")]

# verify result
# df = pl.DataFrame(
#     {
#         "r_number_default": r_number_default,
#         "r_number_tag": r_number_tag,
#         "known": list(known_sequence),
#         "found": list(peptide_data_sequence),
#     }
# )
# df.filter(pl.col("found") != pl.col("known"))


@pytest.mark.parametrize("r_number", [r_number_default, r_number_tag])
def test_check_sequence(r_number):
    n_term = r_number[0]

    records = [
        (r_number[i0], r_number[i1 - 1], peptide_data_sequence[i0:i1])
        for i0, i1 in peptide_intervals_indices
    ]
    df = pl.DataFrame(records, schema=["start", "end", "sequence"], orient="row")

    mismatches = check_sequence(nw.from_native(df), known_sequence, n_term)

    for mismatch, expected in zip(mismatches, expected_mismatches_by_inx):
        idx, c1, c2 = expected
        assert mismatch == (r_number[idx], c1, c2), f"Mismatch at {idx}: expected {c1}, found {c2}"


def test_secb_data_sequence():
    vault = DataVault(cache_dir=TEST_PTH / "datasets")
    ds = vault.load_dataset(DATA_ID)

    for state_name, state in ds.states.items():
        sequence = state.get_sequence()
        pd_peptides = state.peptides["partially_deuterated"].load()

        mismatches = check_sequence(pd_peptides, sequence, n_term=1)
        assert len(mismatches) == 0
