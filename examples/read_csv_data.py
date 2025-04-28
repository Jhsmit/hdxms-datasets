from pathlib import Path
from hdxms_datasets.process import dynamx_cluster_to_state
from hdxms_datasets.reader import read_dynamx
import narwhals as nw


# %%
ROOT = Path(__file__).parent.parent
TEST_PTH = ROOT / "tests"
DATA_ID = "1665149400_SecA_Krishnamurthy"

# read a state data file
csv_file = TEST_PTH / "datasets" / DATA_ID / "data" / "SecA.csv"
csv_dynamx = read_dynamx(csv_file).to_native()
csv_dynamx
# %%

# read a cluster data file, select a single state and convert to state data
csv_file = TEST_PTH / "test_data" / "quiescent state cluster data.csv"
cluster_data = read_dynamx(csv_file)

state = "SecA1-901 wt apo"
cluster_data = cluster_data.filter(nw.col("state") == state)

converted_state_data = dynamx_cluster_to_state(cluster_data)
df_out = converted_state_data.to_native()

print(df_out)

# %%
