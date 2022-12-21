from hdxms_datasets import DataVault

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault()

# Download a specific HDX dataset
vault.fetch_dataset("20221007_1530_SecA_Krishnamurthy")

# Load the dataset
ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")

# Load the FD control of the first 'state' in the dataset.
fd_control = ds.load_peptides(0, "FD_control")

# Load the corresponding experimental peptides.
peptides = ds.load_peptides(0, "experiment")
