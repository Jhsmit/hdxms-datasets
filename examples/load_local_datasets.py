from hdxms_datasets import DataVault
from pathlib import Path

test_pth = Path("../tests").resolve()
data_pth = test_pth / "datasets"
# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

# Load the dataset
ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")

# %%

# Print a string describing the states in the dataset
print(ds.describe())

# Load FD control peptides as a pandas DataFrame
fd_control = ds.load_peptides(0, "FD_control")

# Load experimental peptides as pandas dataframe
peptides = ds.load_peptides(0, "experiment")
