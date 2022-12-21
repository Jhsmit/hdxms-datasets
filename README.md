# HDXMS Datasets


* Free software: MIT license

### Installation

```bash
$ pip install hdxms-datasets
```

### Example code


```python
from hdxms_datasets import DataVault

vault = DataVault()

# Download a specific HDX dataset
vault.fetch_dataset("20221007_1530_SecA_Krishnamurthy")

# Load the dataset
ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")

# Load the FD control of the first 'state' in the dataset.
fd_control = ds.parser.load_peptides(0, 'FD_control')

# Load the corresponding experimental peptides.
peptides = ds.parser.load_peptides(0, 'experiment')

```

