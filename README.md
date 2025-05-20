# HDXMS Datasets


* Free software: MIT license

## Installation

```bash
$ pip install hdxms-datasets
```

## HDX-MS database

Currently a beta test database is set up at:
https://github.com/Jhsmit/HDX-MS-datasets

## Using HDX-MS datasets

### Example code


```python
from pathlib import Path
from hdxms_datasets import DataVault

# local path the download datasets to
cache_dir = Path('.cache')

# create a vault with local cache dir, set `remote_url` to connect to a different database
vault = DataVault(cache_dir=cache_dir)

# Download a specific HDX dataset
vault.fetch_dataset("20221007_1530_SecA_Krishnamurthy")

# Load the dataset
ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")

# Load the FD control of the first 'state' in the dataset.
fd_control = ds.load_peptides(0, "FD_control")

# Load the corresponding experimental peptides.
peptides = ds.load_peptides(0, "experiment")

```

## Web infterface

To run the web interface:
(requires a local clone of the code)

```bash
solara run hdxms_datasets/web/upload_form.py --production
```
