from hdxms_datasets import DataVault

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault()

# Download a specific HDX dataset
vault.fetch_dataset("20221007_1530_SecA_Krishnamurthy")

# Load the dataset
ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")

# Describe the dataset
print(ds.describe())

## Output:
# >>> SecA_monomer:
# >>>  FD_control: 'Total peptides: 188, timepoints: 1'
# >>>  experiment: 'Total peptides: 1273, timepoints: 7'
# >>>  metadata: 'Temperature: 20.0 C, pH: 7.5'

# Load the FD control of the 'SecA_monomer' state .
fd_control = ds.load_peptides('SecA_monomer', "FD_control")

# States can also be referenced by their index, used here to load the peptides corresponding to
# the experiment.
peptides = ds.load_peptides(0, "experiment")
