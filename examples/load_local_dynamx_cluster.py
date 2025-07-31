# %%

# %%
from __future__ import annotations

from pathlib import Path
import polars as pl
from hdxms_datasets.plot import plot_peptides
from hdxms_datasets.process import merge_peptides, compute_uptake_metrics
from hdxms_datasets.database import DataBase
from hdxms_datasets.view import StructureView
# %%

DATASET = "HDX_3BAE2080"  # SecA cluster data

test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
db = DataBase(data_pth)
dataset = db.load_dataset(DATASET)


# %%
# Get the sequence of the first state
state = dataset.states[0]
state.protein_state.sequence

# %%
# check the deutation types of the peptides; we have one
# partially deuterated and one fully deuterated
[p.deuteration_type for p in state.peptides]

# %%
# merge partially deuterated peptides with
# fully deuterated and non deuterated peptides in one dataframe
# this dataframe now has centroid masses for pd, nd, and fd peptides
merged = merge_peptides(state.peptides)
merged.columns

# %%

# compute uptake metrics (uptake, fractional deuterium)
processed = compute_uptake_metrics(merged).to_native()
processed.columns


# %%
# plot the peptides for the first exposure
exposure_value = processed["exposure"].unique()[0]
selected = processed.filter(pl.col("exposure") == exposure_value)

plot_peptides(selected, domain=(0, 1), value="frac_max_uptake")

# %%
peptides = dataset.states[0].peptides[0]
StructureView(dataset.structure).peptide_coverage(peptides)

# %%
# show a set of non-overlapping peptides on the structure
StructureView(dataset.structure).non_overlapping_peptides(peptides)
# %%
