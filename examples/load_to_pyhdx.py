from pyhdx import HDXMeasurement
from hdxms_datasets import DataVault
from pathlib import Path


test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"

vault = DataVault(cache_dir=data_pth)
ds = vault.load_dataset("1665149400_SecA_Krishnamurthy")

hdxm = HDXMeasurement.from_dataset(ds, 0)

print(hdxm)
