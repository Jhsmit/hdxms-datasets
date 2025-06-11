# %%

from hdxms_datasets import RemoteDataVault

# %%

# Creating a RemoveDataVault, specifying a chache dir, using the default remote database
vault = RemoteDataVault(
    cache_dir=".cache",
)
vault.get_index().to_native()

# %%
# Fetch a dataset by ID
vault.fetch_dataset("1704204434_SecB_Krishnamurthy")

# %%
ds = vault.load_dataset("1704204434_SecB_Krishnamurthy")
print(ds.describe())
