from pyhdx import HDXMeasurement
from hdxms_datasets import DataVault
from pathlib import Path


test_pth = Path("../tests").resolve()
data_pth = test_pth / "datasets"

vault = DataVault(cache_dir=data_pth)
ds = vault.load_dataset("20221007_1530_SecB_Krishnamurthy")

hdxm = HDXMeasurement.from_dataset(ds)

print(hdxm)
