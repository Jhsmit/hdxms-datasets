# %%
from __future__ import annotations


import ultraplot as uplt
from pathlib import Path
import numpy as np
import polars as pl
from hdxms_datasets.process import merge_peptides, compute_uptake_metrics
from hdxms_datasets.database import DataBase
from hdxms_datasets.view import StructureView
from hdxms_datasets.verification import compare_structure_peptides

# %%

DATA_ID = "HDX_C1198C76"  # SecA DynamX state data
DATA_ID = "HDX_D9096080"  # SecB DynamX state data

# %%
test_pth = Path(__file__).parent.parent / "tests"
database_dir = test_pth / "datasets"

# %%
db = DataBase(database_dir)
dataset = db.load_dataset(DATA_ID)  # Should load the dataset from the database
print(dataset.description)
# > HDX-MS dataset for SecB protein in tetramer/dimer states
# %%
print([state.name for state in dataset.states])
# > ['Tetramer', 'Dimer']
# %%

state = dataset.states[0]
state.protein_state.sequence  # Get the sequence of the first state

# %%
# check the deutation types of the peptides; we have one
# partially deuterated and one fully deuterated
[p.deuteration_type for p in state.peptides]
# > [<DeuterationType.partially_deuterated: 'partially_deuterated'>, <DeuterationType.fully_deuterated: 'fully_deuterated'>]

# %%

# load the partially deuterated peptides
df = state.peptides[0].load(
    convert=True,
    aggregate=True,
    # sort_rows=True,
    # sort_columns=True,
)
print(df.columns)
# > ['start', 'end', 'sequence', 'state', 'exposure', 'centroid_mz', 'rt', 'rt_sd', 'uptake', 'uptake_sd']
# %%
# merge partially deuterated peptides with
# fully deuterated peptides in one dataframe
merged = merge_peptides(state.peptides)

# compute uptake metrics (uptake, fractional deuterium)
processed = compute_uptake_metrics(merged).to_native()
processed
# %%
# take the first timepoint, plot fractional uptake wrt FD control or max uptake (scaled)
exposure = processed["exposure"].unique()[0]
df = processed.filter(pl.col("exposure") == exposure)
sclf = df["fd_uptake"].mean() / df["max_uptake"].mean()

fig, ax = uplt.subplots(aspect=1.61)
ax.scatter(np.arange(len(df)), df["frac_fd_control"], s=12, c="blue", label="frac_fd_control")
ax.scatter(
    np.arange(len(df)),
    df["frac_max_uptake"] / sclf,
    s=10,
    c="red",
    label="frac_max_uptake",
    marker="*",
)
ax.legend(loc="b", ncols=2)
ax.format(
    ylabel="Relative d-uptake",
    xlabel="Peptide index",
)

# %%
# for .cif structure files only; we can compare how many residues by
# chain and residue number are identical between structure and peptides.

# For the tetramer, some residues are missing in the structure

# We correctly find that the dimer matches fewer residues to the structure
# since we have specified only two of the chains as matching in HDX data
# furthermore, we find that a 3 residues are mutated in the dimer state
# compared to the structure

stats = compare_structure_peptides(
    dataset.structure,
    state.peptides[0],
)
stats
# > {'total_residues': 548, 'matched_residues': 495, 'identical_residues': 495}
# %%

dimer_state = dataset.states[1]
stats, df = compare_structure_peptides(dataset.structure, dimer_state.peptides[0], returns="both")
stats
# > {'total_residues': 282, 'matched_residues': 255, 'correct_residues': 249}

# %%
# show the residues that do not match
df.filter(pl.col("resn_TLA") != pl.col("resn_TLA_right"))

# %%


# %%
# show a single peptide
start, end = processed["start", "end"].row(10)
view = StructureView(dataset.structure).color_peptide(start, end, chain=["A"])
view

# %%
# select a set of peptides for further viusualization
peptides = dataset.states[0].peptides[0]

# %%
# show regions of the structure that are covered by peptides
StructureView(dataset.structure).peptide_coverage(peptides)

# %%
# show a set of non-overlapping peptides on the structure
StructureView(dataset.structure).non_overlapping_peptides(peptides)

# %%
# show peptide redundancy on the structure
StructureView(dataset.structure).peptide_redundancy(peptides)

# %%
