"""
Example script demonstrating how to use the RemoteDataBase class to fetch and load datasets
from a remote HDX-MS database.
"""

# %%

from hdxms_datasets import RemoteDataBase
from pathlib import Path

DATABASE_URL = "https://raw.githubusercontent.com/Jhsmit/HDXMS-database/master/datasets/"

# %%

# create a local directory to store fetched datasets
database_dir = Path().cwd() / "datasets"
database_dir.mkdir(parents=True, exist_ok=True)

# connect to a remote database
# omit the remote_url parameter to use the default
# creating the db will automatically fetch the datasets catalog
db = RemoteDataBase(database_dir, remote_url=DATABASE_URL)
db.datasets_catalog.to_native()

# %%
# fetch the first available dataset, if successful its saved to `database_dir`
data_id = db.remote_datasets[0]
success, message = db.fetch_dataset(data_id)
success, message

# %%
# load the dataset from disk
dataset = db.load_dataset(data_id)
dataset
# %%
