"""
Testing of reader functions.
"""

from pathlib import Path
import polars as pl
from polars.testing import assert_series_equal

TEST_PTH = Path(__file__).parent


def test_read_hdexaminer_peptide_pool():
    from hdxms_datasets.reader import read_hdexaminer_peptide_pool

    f = TEST_PTH / "test_data" / "ecDHFR_tutorial.csv"

    with open(f, "r") as fh:
        exposure_header = fh.readline()

    num_blocks = len([col for col in exposure_header.strip().split(",") if col])

    df_ref = pl.read_csv(f, skip_rows=1, has_header=True)
    df_test = read_hdexaminer_peptide_pool(f).to_polars()

    # number of rows in the parsed dataframe must match num_blocks * rows ref dataframe
    assert len(df_test) == num_blocks * len(df_ref)

    # Check some columns to ensure they match
    columns = ["Start RT", "End RT", "#D", "Score", "Conf"]

    for col_name in columns:
        matching_cols = [col_name] + [
            col for col in df_ref.columns if col.startswith(f"{col_name}_duplicated")
        ]
        dtype = df_ref[col_name].dtype

        series = [df_ref[col].cast(dtype) for col in matching_cols]
        combined = pl.concat(series)

        assert_series_equal(combined, df_test[col_name])
