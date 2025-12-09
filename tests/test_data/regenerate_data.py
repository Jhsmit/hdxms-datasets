"""
Rerun to regenerate processed data reference files for tests
"""

# %%
from hdxms_datasets.database import load_dataset
from pathlib import Path

from hdxms_datasets.process import compute_uptake_metrics, merge_peptides

# %%

cwd = Path(__file__).parent

datasets_dir = cwd.parent / "datasets"
datasets_dir.exists()

dataset_ids = ["HDX_C1198C76", "HDX_3BAE2080", "HDX_2E335A82"]

# %%
for dataset_id in dataset_ids:
    print(f"Processing dataset {dataset_id}")
    dataset = load_dataset(datasets_dir / dataset_id)
    state = dataset.states[0]

    merged = merge_peptides(state.peptides)
    df_test = compute_uptake_metrics(merged, exception="ignore").to_native()

    df_test.write_csv(cwd / f"{dataset_id}_state_0_processed.csv")
    df_test.write_parquet(cwd / f"{dataset_id}_state_0_processed.pq")
