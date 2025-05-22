"""
This script generates test data for the HDXMS datasets.
"""

# %%

from pathlib import Path


from hdxms_datasets.datasets import DataSet
from hdxms_datasets.datavault import DataVault
from hdxms_datasets.reader import read_dynamx

TEST_PTH = Path(__file__).parent.parent
DATA_ID = "1665149400_SecA_Krishnamurthy"

vault = DataVault(cache_dir=TEST_PTH / "datasets")


# %%

ds = vault.load_dataset(DATA_ID)
assert isinstance(ds, DataSet)

states = ds.states
assert states == ["SecA_monomer", "SecA_monomer_ADP", "SecA_WT"]

peptide_dict = ds.load_state(states[0])
df = peptide_dict["experiment"]
df.to_pandas().to_csv("monomer_experimental_peptides.csv", index=False)
# %%

csv_file = TEST_PTH / "datasets" / DATA_ID / "data" / "SecA.csv"
csv_dynamx = read_dynamx(csv_file)
# csv_dynamx.to_csv("read_dynamx_result.csv", index=False)
