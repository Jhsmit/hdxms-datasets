# %%
"""
SecA monomer cluster and state data comparison
There are some differences, both datasets have different peptides/timepoints
and also some peptides differ in their D-uptake values (calculated for cluster data compared to state data)

"""

from hdxms_datasets import DataVault
from pathlib import Path

from hdxms_datasets.process import merge_peptides, compute_uptake_metrics
import ultraplot as uplt
import numpy as np
import polars as pl
import narwhals as nw


# %%
test_pth = Path(__file__).parent.parent.parent / "tests"
data_pth = test_pth / "datasets"

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

ds = vault.load_dataset("1744801204_SecA_cluster_Krishnamurthy")
nd_control = ds.get_peptides(0, "non_deuterated").load()
fd_control = ds.get_peptides(0, "fully_deuterated").load()
pd_peptides = ds.get_peptides(0, "partially_deuterated").load()

merged = merge_peptides(pd_peptides, non_deuterated=nd_control, fully_deuterated=fd_control)
processed_cluster = compute_uptake_metrics(merged)
processed_cluster.to_native()

# %%
ds = vault.load_dataset("1665149400_SecA_Krishnamurthy")
fd_control = ds.get_peptides(0, "fully_deuterated").load()
pd_peptides = ds.get_peptides(0, "partially_deuterated").load()

merged = merge_peptides(pd_peptides, fully_deuterated=fd_control)
processed_state = compute_uptake_metrics(merged)
processed_state.to_native()

# %%
# compare left and right exposure start/end points
cluster_datapoints = set(processed_cluster[["start", "end", "exposure"]].iter_rows())
state_datapoints = set(processed_state[["start", "end", "exposure"]].iter_rows())

len(cluster_datapoints), len(state_datapoints), len(cluster_datapoints & state_datapoints)

# %%
# compare left and right start/end points

cluster_datapoints = set(processed_cluster[["start", "end"]].iter_rows())
state_datapoints = set(processed_state[["start", "end"]].iter_rows())

len(cluster_datapoints), len(state_datapoints), len(cluster_datapoints & state_datapoints)

# %%

# %%
combined = processed_cluster.join(
    processed_state,
    on=["start", "end", "exposure"],
    how="inner",
    suffix="_state",
)
combined.to_native()

# %%
col = "uptake"
v1 = combined[col]
v2 = combined[f"{col}_state"]

np.max(np.abs(v1 - v2))

imax = np.argmax(np.abs(v1 - v2))

combined[imax.item()].to_native()

# %%

diffs = np.array(v1 - v2)
m = np.mean(diffs)
s = np.std(diffs)

bins = np.linspace(m - 5 * s, m + 5 * s, 100)

# %%
matching_columns = [col for col in combined.columns if col + "_state" in combined.columns]
len(matching_columns)

matching_numerical = [
    col for col in matching_columns if isinstance(combined[col].dtype, nw.dtypes.NumericType)
]
len(matching_numerical)
# %%

col = "uptake"
abs_diff = np.abs(combined[col] - combined[f"{col}_state"])

tolerance = np.logspace(-8, 0, 100)
num_deviating = np.greater_equal(abs_diff, tolerance[:, None]).sum(axis=1)

# %%
fig, ax = uplt.subplots()
ax.plot(tolerance, num_deviating)
ax.format(
    xlabel="Tolerance",
    ylabel="Number of Deviating Values",
    xscale="log",
    xformatter="log",
    title="Number of Deviating Values vs Tolerance",
)

# %%

tol_thd = 10e-4
idx = np.argwhere(abs_diff > tol_thd).squeeze()
df_deviating = combined[list(idx)].to_native()[
    "state", "start", "end", "sequence", "charge", "exposure", "uptake", "uptake_state"
]

df_deviating = df_deviating.with_columns(
    (pl.col("uptake") - pl.col("uptake_state")).alias("diff")
).sort("diff")
df_deviating = df_deviating.with_columns((pl.col("diff") / pl.col("uptake")).alias("diff_pct"))
df_deviating
# %%
col = matching_columns[1]
fig, axes = uplt.subplots(ncols=3, nrows=3, share=False)

for ax, col in zip(axes, matching_numerical):
    v1 = combined[col]
    v2 = combined[f"{col}_state"]
    diffs = np.array(v1 - v2)
    m = np.mean(diffs)
    s = np.std(diffs)
    bins = np.linspace(m - 5 * s, m + 5 * s, 100)
    ax.hist(diffs, bins=bins)
    ax.format(title=col)
# %%

combined.to_polars().describe()
# %%
