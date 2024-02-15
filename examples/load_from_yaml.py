from hdxms_datasets import DataSet
from pathlib import Path
import yaml


test_pth = Path(__file__).parent.parent / "tests"
data_pth = test_pth / "datasets"
data_id = "1665149400_SecA_Krishnamurthy"

hdx_spec = yaml.safe_load((data_pth / data_id / "hdx_spec.yaml").read_text())
metadata = yaml.safe_load((data_pth / data_id / "metadata.yaml").read_text())

# %%

dataset = DataSet.from_spec(hdx_spec, data_dir=data_pth / data_id, metadata=metadata)

print(dataset.describe())
