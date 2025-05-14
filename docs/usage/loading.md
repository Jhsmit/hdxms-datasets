# Loading Datasets

The `hdxms_datasets` package features a central `DataVault` object, which is used to fetch datasets from an online 
database to a local cache dir, as well as parse those locally saved peptide sets into a narwhals `DataFrame`.

## Basic usage

```python

# Creating a RemoveDataVault, specifying a chache dir, using the default remote database
vault = RemoteDataVault(
    cache_dir=".cache",
)
vault.get_index().to_native()

#%%
# Fetch a dataset by ID
vault.fetch_dataset("1704204434_SecB_Krishnamurthy")

# Load the dataset
ds = vault.load_dataset("1704204434_SecB_Krishnamurthy")

# Print a string describing the states in the dataset
print(ds.describe())

# Load ND control peptides as a narwhals DataFrame
nd_control = ds.get_peptides(0, "non_deuterated").load()

# # Load FD control peptides as a narwhals DataFrame
fd_control = ds.get_peptides(0, "fully_deuterated").load()

# Load experimental peptides as narwhals dataframe
pd_peptides = ds.get_peptides(0, "partially_deuterated").load()
pd_peptides
# %%
# Merge peptides, matching each partially dueterated peptide timepoint with nd/fd control uptake or mass
merged = merge_peptides(pd_peptides, nd_peptides=nd_control, fd_peptides=fd_control)

# %%

# compute d-uptake, max uptake, full deuteration uptake, RFU
processed = compute_uptake_metrics(merged)
processed.to_native()

```

The code above creates a `RemoteDataVault`, thereby creating a cache directory. Then the dataset `"1704204434_SecB_Krishnamurthy"` is fetched  from the database and stored in the cache dir.

From here, HDX-MS data can be loaded and processed. 