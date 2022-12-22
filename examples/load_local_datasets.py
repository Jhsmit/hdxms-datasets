from hdxms_datasets import DataVault
from pathlib import Path

test_pth = Path("../tests").resolve()
data_pth = test_pth / "datasets"
# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
vault = DataVault(data_pth)

# Load the dataset
ds = vault.load_dataset("20221007_1530_SecA_Krishnamurthy")

#%%

import hashlib

print(ds.describe())


#%%

s = """SecA_monomer:
  FD_control: 'Total peptides: 188, timepoints: 1'
  experiment: 'Total peptides: 1273, timepoints: 7'
  metadata: 'Temperature: 20.0 C, pH: 7.5'
SecA_monomer_ADP:
  FD_control: 'Total peptides: 188, timepoints: 1'
  experiment: 'Total peptides: 1267, timepoints: 7'
  metadata: 'Temperature: 20.0 C, pH: 7.5'
SecA_WT:
  FD_control: 'Total peptides: 186, timepoints: 1'
  experiment: 'Total peptides: 1316, timepoints: 7'
  metadata: 'Temperature: 20.0 C, pH: 7.5'
"""

s == ds.describe()

#s

#%%

df = ds.peptide_sets["SecA_monomer"]["FD_control"]

"TKVFGSRND" in df['sequence']
len(df)

#%%

# FD_control: 'Total peptides: 185, timepoints: 1'
# experiment: 'Total peptides: 1316, timepoints: 7'

