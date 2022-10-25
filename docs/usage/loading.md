# Loading Datasets

The `hdxms_datasets` package features a central `DataVault` object, which is used to fetch datasets from an online 
database, as well as parse those locally saved datasets into either a pandas `DataFrame` or other formats from external 
libraries.

## Basic usage

```python
from hdxms_datasets import DataVault

vault = DataVault()
vault.fetch_dataset("20221007_1530_SecA_Krishnamurthy")

ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")

fd_control = ds.parser.load_peptides(0, "FD_control") 
peptides = ds.parser.load_peptides(0, 'experiment')

```

The code above initiates a `DataVault` object, thereby creating a cache directory in the default location 
(`~/.hdxms_datasets`) if it does not yet exist. Then the dataset `"20221007_1530_SecA_Krishnamurthy"` is fetched 
from the database and stored in the cache dir.

`Datavault.load_dataset` loads the dataset which is returned as `HDXDataSet` object. This object has a `StateParser` instance as the `parser`attribute 
which can be used to select protein states as defined in this dataset (here the first state is selected), and within 
this state users can choose defined sets of peptides. In this example both the peptides belonging to the fully deuterated
control and the 'experiment' peptides are loaded and returned as pandas `DataFrame`. 
