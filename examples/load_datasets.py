# %%
from hdxms_datasets import RemoteDataVault
from pathlib import Path

# %%
# create a data vault, specify cache_dir to download datasets to
cache_dir = Path.home() / ".hdxms_datasets"
vault = RemoteDataVault(cache_dir=cache_dir)
vault

# %%
# Download a specific HDX dataset
vault.fetch_dataset("1665149400_SecA_Krishnamurthy")
vault.datasets

# %%
# Load the dataset
ds = vault.load_dataset("1665149400_SecA_Krishnamurthy")

# Describe the dataset
print(ds.describe())

# Load the FD control of the 'SecA_monomer' state .
fd_control = ds.get_peptides("SecA_monomer", "FD_control")


# States can also be referenced by their index, used here to load the peptides corresponding to
# the experiment.
peptides = ds.get_peptides(0, "partially_deuterated")
peptides.load()

# %%
