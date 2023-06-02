from hdxms_datasets import DataFile, HDXDataSet
from pathlib import Path
import yaml

from hdxms_datasets.process import parse_data_files

test_pth = Path("../tests").resolve()
data_pth = test_pth / "datasets"
data_id = '20221007_1530_SecA_Krishnamurthy'

hdx_spec = yaml.safe_load((data_pth / data_id / "hdx_spec.yaml").read_text())
metadata = yaml.safe_load((data_pth / data_id / "metadata.yaml").read_text())
hdx_spec['data_files']

#%%
data_files = parse_data_files(hdx_spec['data_files'], data_pth / data_id)

#%%
data_file = DataFile(
    name='data_1',
    format='DynamX',
    filepath_or_buffer=data_pth / data_id / "data" / "SecA.csv"
)

# Read the data as dataframe
df = data_file.data

dataset = HDXDataSet(
    data_id = 'my_dataset',
    data_files = {data_file.name: data_file},
    hdx_spec = hdx_spec,
    metadata=metadata
)

print(dataset.describe())