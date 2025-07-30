# %%
"""convert v 0.2.x datasets to v 0.3.x dataset"""

from hdxms_datasets.database import submit_dataset
from hdxms_datasets.models import (
    Author,
    HDXDataSet,
    HDXState,
    ProteinIdentifiers,
    ProteinState,
    Structure,
    DatasetMetadata,
)
import polars as pl
import narwhals as nw
from pathlib import Path
import yaml
from hdxms_datasets.migration.v020 import get_peptides
from hdxms_datasets.utils import reconstruct_sequence, verify_sequence
# %%

root = Path(__file__).parent
yaml_file = root / "hdx_spec.yaml"
hdx_spec = yaml.safe_load(yaml_file.read_text())
hdx_spec
# %%
pub = None  # unpublished

# %%

metadata = DatasetMetadata(
    authors=[Author(name="Vladimir Sarpe")],
    conversion_notes="Converted from HDX-MS v0.2.x to v0.3.x",
)

protein_info = ProteinIdentifiers(
    uniprot_accession_number="P00004",
    uniprot_entry_name="CYC_HORSE",
)

structure = Structure(
    data_file=root.parent / "data/1akk.pdb",
    format="pdb",
    description="NMR minimized average structure",
    pdb_id="1AKK",
    residue_offset=-1,  # HDX data has an additional n terminal Methionine residue
)

# %%

pth = root.parent / "data" / "data_file.csv"
df = pl.read_csv(pth)
df = nw.from_native(df)
reconstruct_sequence(df, "X" * (df["End"].max() + 1), start="Start", end="End", sequence="Sequence")

# %%
sequence = "MGDVEKGKKIFVQKCAQCHTVEKGGKHKTGPNLHGLFGRKTGQAPGFTYTDANKNKGITWKEETLMEYLENPKKYIPGTKMIFAGIKKKTEREDLIAYLKKATNEXXXX"
verify_sequence(df, sequence, start="Start", end="End", sequence="Sequence")  # sequence OK
# %%
states = list(hdx_spec["peptides"].keys())
states
# %%

hdx_states = []
for state in states:
    peptide_spec = hdx_spec["peptides"][state]
    peptides = get_peptides(peptide_spec, hdx_spec["data_files"], root_dir=root.parent)

    for peptide in peptides:
        mismatches = verify_sequence(peptide.load(), sequence)
        if mismatches:
            print(f"Peptide {peptide.data_file} has mismatches: {mismatches}")

    protein_state = ProteinState(
        sequence=sequence,
        n_term=1,
        c_term=len(sequence),
        oligomeric_state=1,
    )

    hdx_state = HDXState(
        name=state,
        protein_state=protein_state,
        peptides=peptides,
    )

    hdx_states.append(hdx_state)

hdx_states

# %%

dataset = HDXDataSet(
    description="cyt c hd examiner example data",
    states=hdx_states,
    structure=structure,
    protein_identifiers=protein_info,
    metadata=metadata,
)

s = dataset.model_dump_json(indent=2, exclude_none=True)
Path(root.parent / "dataset.json").write_text(s)

database_dir = root.parent
# submit the dataset to our database
success, msg_or_id = submit_dataset(dataset, database_dir)
if success:
    print(f"Dataset submitted successfully with ID: {msg_or_id}")
else:
    print(f"Failed to submit dataset: {msg_or_id}")


# %%
