# %%

from pathlib import Path

from hdxms_datasets import DataVault
from hdxms_datasets.process import compute_uptake_metrics, merge_peptides

# %%
test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

# Load the dataset
ds = vault.load_dataset("1744801204_SecA_cluster_Krishnamurthy")

# %%

# Print a string describing the states in the dataset
print(ds.describe())

# Load ND control peptides as a narwhals DataFrame
nd_control = ds.get_peptides(0, "non_deuterated").load()

# # Load FD control peptides as a narwhals DataFrame
fd_control = ds.get_peptides(0, "fully_deuterated").load()

# Load experimental peptides as narwhals dataframe
pd_peptides = ds.get_peptides(0, "partially_deuterated").load()
pd_peptides
# %%
merged = merge_peptides(pd_peptides, nd_peptides=nd_control, fd_peptides=fd_control)

# %%
processed = compute_uptake_metrics(merged)
processed.to_native()

# %%
