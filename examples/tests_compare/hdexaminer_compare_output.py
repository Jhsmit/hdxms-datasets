# %%
from pathlib import Path

import narwhals as nw
import numpy as np
import ultraplot as uplt

from hdxms_datasets import DataVault
from hdxms_datasets.process import (
    aggregate_columns,
    compute_uptake_metrics,
    merge_peptides,
)
from hdxms_datasets.convert import from_hdexaminer

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

pd_peptides = ds.get_peptides(0, "partially_deuterated").load(
    convert=True, aggregate=True, sort=True
)
# %%
merged = merge_peptides(pd_peptides, non_deuterated=nd_control, fully_deuterated=fd_control)

# %%
processed = compute_uptake_metrics(merged)
processed.to_native()
# %% load the original data, process to match
raw_df = ds.data_files["data_1"].read()


cols = ["# Deut", "Deut %"]
df_hdxe = from_hdexaminer(raw_df, extra_columns=cols)

df = (
    df_hdxe.filter(nw.col("state") == "D90")
    .filter(nw.col("exposure") != "0s")
    .filter(nw.col("exposure") != "FD")
)
df = df.with_columns(nw.col("exposure").str.strip_chars("s").cast(nw.Float64))
df = df.filter(nw.col("Deut %") != "n/a")
df = df.with_columns([nw.col(col).cast(nw.Float64) for col in cols])

df.to_native()

# %%
# aggregate columns
columns = ["# Deut", "Deut %"]
agg_df = aggregate_columns(df, columns=columns)
agg_df.to_native()

# %%
# map onto original result
combined = processed.join(
    agg_df,
    on=["start", "end", "exposure"],
    how="left",
)
combined.to_native()

# %%

cols = ["# Deut", "uptake"]
df_s = combined.select(cols)
for col in cols:
    df_s = df_s.filter(~nw.col(col).is_nan())

v1 = df_s["# Deut"]
v2 = df_s["uptake"] / 0.9
fig, axes = uplt.subplots(nrows=1, ncols=2, share=False)
axes[0].scatter(v1, v2)
axes[0].format(xlabel="# Deut", ylabel="Uptake", xlim=(0, 10), ylim=(0, 10))
axes[1].hist(v1 - v2, bins="fd")
axes[1].format(xlim=(-0.02, 0.02), xlabel="# Deut - Uptake")

rmse = ((v1 - v2) ** 2).mean() ** 0.5
# %%

cols = ["Deut %", "rfu"]
df_s = combined.select(cols)
for col in cols:
    df_s = df_s.filter(~nw.col(col).is_nan())

v1 = df_s["Deut %"]
v2 = df_s["rfu"] * 100
fig, axes = uplt.subplots(nrows=1, ncols=2, share=False)
axes[0].scatter(v1, v2)
axes[0].format(xlim=(0, 110), ylim=(0, 110), xlabel="Deut %", ylabel="RFU (%)")
axes[1].hist(v1 - v2, bins="fd")
axes[1].format(xlim=(-0.1, 0.1), xlabel="Deut % - RFU (%)")

# %%

rmse = ((v1 - v2) ** 2).mean() ** 0.5
rmse

# %%
rse = np.sqrt((v1 - v2) ** 2)
idx = np.argwhere(rse > 1).squeeze()
# %%
# looks like there are 4 peptide timepoints which deviate
combined[list(idx)].to_native()
