# %%

from hdxms_datasets import DataVault
from pathlib import Path


# %%
test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

# Load the dataset
ds = vault.load_dataset("1665149400_SecA_Krishnamurthy")
print(ds.describe())
# %%

# # Load FD control peptides as a narwhals DataFrame
fd_control = ds.get_peptides(0, "fully_deuterated").load(aggregate=False)
print(fd_control)
# %%

# Load partially deuterated peptides as narwhals dataframe
pd_peptides = ds.get_peptides(0, "partially_deuterated").load(aggregate=False)
pd_peptides
