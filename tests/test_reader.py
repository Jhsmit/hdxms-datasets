from pathlib import Path
from hdxms_datasets.reader import read_dynamx
import pandas as pd

TEST_PTH = Path(__file__).parent
DATA_ID = "1665149400_SecA_Krishnamurthy"


def test_read_dynamx():
    csv_file = TEST_PTH / "datasets" / DATA_ID / "data" / "SecA.csv"
    df = read_dynamx(csv_file)

    df_ref = pd.read_csv(TEST_PTH / "test_data" / "read_dynamx_result.csv")
    pd.testing.assert_frame_equal(df, df_ref)
