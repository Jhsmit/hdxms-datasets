from hdxms_datasets import load_dataset
from pathlib import Path

DATA_ID = "HDX_C1198C76"  # SecA DynamX state data
DATA_ID = "HDX_D9096080"  # SecB DynamX state data

fname = "HDX_3BAE2080.zip"  # Example dataset in a zip file

# %%
test_pth = Path(__file__).parent.parent / "tests"
database_dir = test_pth / "datasets"

dataset = load_dataset(database_dir / fname)  # Should load the dataset from the zip file

print(dataset.states)

# %%
