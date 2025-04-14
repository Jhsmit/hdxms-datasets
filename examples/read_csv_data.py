from pathlib import Path
from hdxms_datasets.reader import read_dynamx


# %%
ROOT = Path(__file__).parent.parent
TEST_PTH = ROOT / "tests"
DATA_ID = "1665149400_SecA_Krishnamurthy"
csv_file = TEST_PTH / "datasets" / DATA_ID / "data" / "SecA.csv"
csv_dynamx = read_dynamx(csv_file).to_native()


csv_dynamx
# %%
