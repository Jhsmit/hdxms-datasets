from pathlib import Path

from hdxms_datasets import cfg, DataVault

test_pth = Path("../tests").resolve()
data_pth = test_pth / "datasets"
# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

cfg.time_unit = 'min'

ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")
# Print a string describing the states in the dataset
print(ds.describe())

# Load FD control peptides as a pandas DataFrame
fd_control = ds.load_peptides(0, "FD_control")

print(fd_control['exposure'].unique())

#%%
