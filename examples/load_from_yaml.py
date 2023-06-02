from hdxms_datasets import DataFile, HDXDataSet
from pathlib import Path
import yaml

from hdxms_datasets.process import parse_data_files

test_pth = Path("../tests").resolve()
data_pth = test_pth / "datasets"
data_id = '20221007_1530_SecA_Krishnamurthy'

hdx_spec = yaml.safe_load((data_pth / data_id / "hdx_spec.yaml").read_text())
metadata = yaml.safe_load((data_pth / data_id / "metadata.yaml").read_text())

#%%

dataset = HDXDataSet.from_spec(
    hdx_spec,
    data_dir=data_pth / data_id,
    metadata=metadata
)

print(dataset.describe())