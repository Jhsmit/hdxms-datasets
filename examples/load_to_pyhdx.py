from pyhdx import StateParser as PyHDXParser
from hdxms_datasets.datasets import DataVault


vault = DataVault(parser=PyHDXParser)

ds = vault.load_dataset("20221007_1530_SecB_Krishnamurthy")

hdxm = ds.parser.load_hdxm(0)

print(hdxm)