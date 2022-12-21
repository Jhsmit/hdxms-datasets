# Loading Datasets

The `hdxms_datasets` package features a central `DataVault` object, which is used to fetch datasets from an online 
database to a local cache dir, as well as parse those locally saved peptide sets into a pandas `DataFrame`.

## Basic usage

```python
from hdxms_datasets import DataVault

vault = DataVault()
vault.fetch_dataset("20221007_1530_SecA_Krishnamurthy")

ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")

fd_control = ds.load_peptides(0, "FD_control") 
peptides = ds.load_peptides(0, 'experiment')

```

The code above initiates a `DataVault` object, thereby creating a cache directory in the default location 
(`~/.hdxms_datasets`) if it does not yet exist. Then the dataset `"20221007_1530_SecA_Krishnamurthy"` is fetched 
from the database and stored in the cache dir.

`Datavault.load_dataset` loads the dataset which is returned as `HDXDataSet` object. From the `HDXDataSet` object, 
users can load peptides from the available states. In the example above, the Fully Deuterated control peptides are loaded
from the first HDX state as a pandas `DataFrame`. The experimental peptides are loaded in the same way.
