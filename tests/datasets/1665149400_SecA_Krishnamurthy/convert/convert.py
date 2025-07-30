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
    Publication,
)

from pathlib import Path
import yaml
from hdxms_datasets.utils import verify_sequence
from hdxms_datasets.migration.v020 import get_peptides
from hdxms_datasets.verification import verify_dataset
# %%

root = Path(__file__).parent
yaml_file = root / "hdx_spec.yaml"
hdx_spec = yaml.safe_load(yaml_file.read_text())

# %%

pub = Publication(
    title="A nexus of intrinsic dynamics underlies translocase priming",
    doi="10.1016/j.str.2021.03.015",
    url="https://www.sciencedirect.com/science/article/pii/S0969212621001131",
)

# %%

metadata = DatasetMetadata(
    authors=[
        Author(name="Srinath Krishnamurthy", orcid="0000-0001-5492-4450", affiliation="KU Leuven")
    ],
    conversion_notes="Converted from HDX-MS v0.2.x to v0.3.x",
)

protein_info = ProteinIdentifiers(
    uniprot_accession_number="P10408",
    uniprot_entry_name="SECA_ECOLI",
)

structure = Structure(
    data_file=root / "SecA_monomer.pdb",
    format="pdb",
    description="NMR structure with ligand removed in sillico",
    pdb_id="2VDA",
)

# %%
orig_states = list(hdx_spec["peptides"].keys())
# set WT apo as first state
states = orig_states[1::2] + orig_states[::2]

# %%

hdx_states = []
for state in states:
    protein_spec = hdx_spec["protein"][state]
    peptide_spec = hdx_spec["peptides"][state]

    peptides = get_peptides(peptide_spec, hdx_spec["data_files"], root_dir=root.parent, chain=["B"])

    # we only keep the FD control for the WT apo state; other states should use the same one
    if state != "SecA-WT_apo":
        peptides = [p for p in peptides if p.deuteration_type != "fully_deuterated"]
        print(state, len(peptides))
    protein_state = ProteinState(
        **protein_spec,
    )

    hdx_state = HDXState(
        name=state,
        protein_state=protein_state,
        peptides=peptides,
    )

    hdx_states.append(hdx_state)

# %%

dataset = HDXDataSet(
    description="SecA quiescent states dataset",
    states=hdx_states,
    structure=structure,
    protein_identifiers=protein_info,
    metadata=metadata,
)

verify_dataset(dataset)

# %%

database_dir = root.parent
# submit the dataset to our database
success, msg_or_id = submit_dataset(dataset, database_dir)
if success:
    print(f"Dataset submitted successfully with ID: {msg_or_id}")
else:
    print(f"Failed to submit dataset: {msg_or_id}")

# %%
