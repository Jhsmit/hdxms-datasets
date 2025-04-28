# %%

from hdxms_datasets import DataVault
from pathlib import Path


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

# # Load FD control peptides as a narwhals DataFrame
fd_control = ds.get_peptides(0, "fully_deuterated").load()

# Load experimental peptides as narwhals dataframe
peptides = ds.get_peptides(0, "partially_deuterated").load()
