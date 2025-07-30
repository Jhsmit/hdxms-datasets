# %%
"""convert v 0.2.x datasets to v 0.3.x dataset"""

from hdxms_datasets.v2.models import (
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
from hdxms_datasets.v2.migration.v020 import get_peptides
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
    data_file=Path("data/SecA_monomer.pdb"),
    format="pdb",
    description="NMR structure with ligand removed in sillico",
    pdb_id="2VDA",
)

# %%
states = list(hdx_spec["peptides"].keys())

# %%


states_mapping = {
    "WT ADP": "SecA-WT_ADP",
    "Monomer ADP": "SecA-monomer_ADP",
    "1-834 ADP": "SecA-1-834_ADP",
    "WT apo": "SecA-WT_apo",
    "Monomer apo": "SecA-monomer_apo",
    "1-834 apo": "SecA-1-834_apo",
}


# %%

# load the seca state data as reference for protein data
seca_state_dir = root.parent.parent / "1665149400_SecA_Krishnamurthy"
json_str = (seca_state_dir / "dataset.json").read_text()

# %%
ds_state = HDXDataSet.model_validate_json(json_str)
wt_state = ds_state.get_state("SecA-WT_ADP")
wt_state.protein_state
# %%

hdx_states = []
for state in states:
    peptide_spec = hdx_spec["peptides"][state]
    peptides = get_peptides(peptide_spec, hdx_spec["data_files"])
    new_state_name = states_mapping[state]

    ref_state = ds_state.get_state(new_state_name)

    hdx_state = HDXState(
        name=state,
        protein_state=ref_state.protein_state,
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

s = dataset.model_dump_json(indent=2, exclude_none=True)
Path(root.parent / "dataset.json").write_text(s)

# %%
