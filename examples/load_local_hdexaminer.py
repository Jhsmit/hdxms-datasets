# %%
from hdxms_datasets import DataVault
from pathlib import Path

from hdxms_datasets.process import merge_peptides, compute_uptake_metrics

# %%
test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

# Load the dataset
ds = vault.load_dataset("1745478702_hd_examiner_example_Sharpe")

# %%
# Print a string describing the states in the dataset
print(ds.describe())

nd_control = ds.get_peptides(0, "non_deuterated").load()

# Load FD control peptides as a narwhals DataFrame
fd_control = ds.get_peptides(0, "fully_deuterated").load()

# Load experimental peptides as narwhals dataframe
# columns are converted to open-hdxms format
# data is aggregated by replicate (intensity weighted mean)
# and sorted by start, end, exposure
pd_peptides = ds.get_peptides(0, "partially_deuterated").load(
    convert=True, aggregate=True, sort=True
)
pd_peptides.columns

# %%
merged = merge_peptides(pd_peptides, nd_peptides=nd_control, fd_peptides=fd_control)

# %%
processed = compute_uptake_metrics(merged)
df = processed.to_native()
print(df)
# %%
