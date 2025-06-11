# %%
from hdxms_datasets import DataVault
from pathlib import Path

from hdxms_datasets.datasets import allow_missing_fields
from hdxms_datasets.process import merge_peptides, compute_uptake_metrics

# %%

DATASET = "1745478702_hd_examiner_example_Sharpe"

test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

# Load the dataset
# we allow for missing protein info (sequence information) since this dataset does not define it
with allow_missing_fields():
    ds = vault.load_dataset(DATASET)

# %%
# Print a string describing the states in the dataset
print(ds.describe())

# Get the seqeunce of the first state
state = ds.get_state(0)
sequence = state.get_sequence()
print(sequence)

# %%
# Load ND control peptides as a narwhals DataFrame
nd_control = state.get_peptides("non_deuterated").load()

# Load FD control peptides as a narwhals DataFrame
fd_control = state.get_peptides("fully_deuterated").load()

# Load partially deuterated peptides as narwhals dataframe
pd_peptides = state.get_peptides("partially_deuterated").load()
pd_peptides

# %%
# merge controls with partially deuterated peptides
merged = merge_peptides(pd_peptides, non_deuterated=nd_control, fully_deuterated=fd_control)

# compute uptake metrics (uptake, rfu)
processed = compute_uptake_metrics(merged)
df = processed.to_native()
print(df)

# do the previous two steps in one go
processed = state.compute_uptake_metrics().to_polars()
print(processed)
