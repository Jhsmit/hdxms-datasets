# %%
from pathlib import Path
import narwhals as nw
from hdxms_datasets.plot import plot_peptides
from hdxms_datasets.process import merge_peptides, compute_uptake_metrics
from hdxms_datasets.database import DataBase
from hdxms_datasets.view import StructureView
# %%

DATASET = "HDX_3C3CF77E"  # hd examiner data

test_pth = Path(__file__).parent.parent / "tests"
database_dir = test_pth / "datasets_private"

# Creating a DataVault without giving a cache path name uses $home/.hdxms_datasets by default
db = DataBase(database_dir)
dataset = db.load_dataset(DATASET)  # Should load the dataset from the database

# %%
state = dataset.states[0]
state.protein_state.sequence  # Get the sequence of the first state
# %%
merged = merge_peptides(state.peptides)
# %%
# merge controls with partially deuterated peptides
merged = merge_peptides(state.peptides)

# compute uptake metrics (uptake, rfu)
processed = compute_uptake_metrics(merged)
df = processed.to_native()
print(df)

# %%
exposure_value = processed["exposure"].unique()[0]
selected = processed.filter(nw.col("exposure") == exposure_value)
plot_peptides(selected.to_polars(), value="frac_max_uptake", domain=(0, 1))
# %%

peptides = dataset.states[0].peptides[0]
StructureView(dataset.structure).peptide_coverage(selected)
