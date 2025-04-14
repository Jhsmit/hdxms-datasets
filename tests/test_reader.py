from pathlib import Path
from hdxms_datasets.reader import read_dynamx
import polars as pl
from polars.testing import assert_frame_equal

TEST_PTH = Path(__file__).parent
DATA_ID = "1665149400_SecA_Krishnamurthy"


def test_read_dynamx():
    csv_file = TEST_PTH / "datasets" / DATA_ID / "data" / "SecA.csv"
    df = pl.DataFrame(read_dynamx(csv_file))

    df_ref = pl.read_csv(TEST_PTH / "test_data" / "read_dynamx_result.csv")
    assert_frame_equal(df.drop_nans("uptake"), df_ref.drop_nulls("uptake"))
