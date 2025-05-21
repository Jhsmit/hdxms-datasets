# %%

from hdxms_datasets import DataVault
from pathlib import Path

from hdxms_datasets.process import merge_peptides, compute_uptake_metrics

DATASET = "1665149400_SecA_Krishnamurthy"

# %%
test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

# Load the dataset
ds = vault.load_dataset(DATASET)
print(ds.describe())
# %%

# Load FD control peptides as a narwhals DataFrame
fd_control = ds.get_peptides(0, "fully_deuterated").load(aggregate=False)
# Load partially deuterated peptides as narwhals dataframe
pd_peptides = ds.get_peptides(0, "partially_deuterated").load(aggregate=False)


# %%
merged = merge_peptides(pd_peptides, fully_deuterated=fd_control)
merged.to_native()

# %%

processed = compute_uptake_metrics(merged)
processed.to_native()

# %%

# do the previous two steps in one go
processed = ds.compute_uptake_metrics(0).to_polars()
processed.write_parquet(
    "dynamx_state.pq",
)
