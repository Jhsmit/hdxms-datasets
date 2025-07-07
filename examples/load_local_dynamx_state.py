# %%
from hdxms_datasets import DataVault
from pathlib import Path

from hdxms_datasets.backend import BACKEND
from hdxms_datasets.process import merge_peptides, compute_uptake_metrics
import narwhals as nw


DATASET = "1665149400_SecA_Krishnamurthy"
# DATASET = "1704204434_SecB_Krishnamurthy"

# %%
test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"
# %%
# DATASET = "1665149400_SecA_Krishnamurthy"
vault = DataVault(data_pth)

# %%
# Load the dataset
ds = vault.load_dataset(DATASET)

# Print a string describing the states in the dataset
print(ds.describe())
# %%
# Get the sequence of the first state
state = ds.get_state(0)
sequence = state.get_sequence()
print(sequence)

# %%
# Load FD control peptides as a narwhals DataFrame
fd_control = state.get_peptides("fully_deuterated").load()

# Load partially deuterated peptides as narwhals dataframe
pd_peptides = state.get_peptides("partially_deuterated").load()
pd_peptides

pd_peptides.to_native()


# %%
# merge controls with partially deuterated peptides
merged = merge_peptides(pd_peptides, fully_deuterated=fd_control)

# compute uptake metrics (uptake, rfu)
processed = compute_uptake_metrics(merged)
df = processed.to_native()
print(df)

# do the previous two steps in one go
processed = state.compute_uptake_metrics().to_polars()
processed

# %%
# show the first peptide on the structure
start, end = processed["start", "end"].row(10)
view = state.structure.pdbemolstar().color_peptide(start, end)
view

# %%
# show regions of the structure that are covered by peptides
pdbemolstar = state.structure.pdbemolstar()
view = pdbemolstar.peptide_coverage(processed, color="blue")
view

# %%
# show a set of non-overlapping peptides on the structure
view = pdbemolstar.non_overlapping_peptides(processed)
view

# %%
view = pdbemolstar.peptide_redundancy(processed)
view
