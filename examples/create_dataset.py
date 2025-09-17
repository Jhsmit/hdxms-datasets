# %%
from __future__ import annotations
from pathlib import Path

from hdxms_datasets.database import submit_dataset
from hdxms_datasets.models import (
    DatasetMetadata,
    HDXDataSet,
    State,
    DeuterationType,
    Author,
    PeptideFormat,
    Peptides,
    ProteinIdentifiers,
    ProteinState,
    Publication,
    Structure,
)
from hdxms_datasets.utils import verify_sequence
# %%

cwd = Path(__file__).parent

# directory with current data
data_dir = cwd / "test_data"

# directory where to publish the dataset
database_dir = cwd / "published_datasets"
database_dir.mkdir(exist_ok=True)


# %%
# define protein and structure
protein_info = ProteinIdentifiers(
    uniprot_accession_number="P0AG86",
    uniprot_entry_name="SECB_ECOLI",
)

structure = Structure(
    data_file=data_dir / "SecB_structure.pdb",
    format="pdb",
    description="Crystal structure of E. coli SecB protein",
)

# %%
# state: tetramer
protein_state = ProteinState(
    sequence="MSEQNNTEMTFQIQRIYTKDISFEAPNAPHVFQKDWQPEVKLDLDTASSQLADDVYEVVLRVTVTASLGEETAFLCEVQQGGIFSIAGIEGTQMAHCLGAYCPNILFPYARECITSMVSRGTFPQLNLAPVNFDALFMNYLQQQAGEGTEEHQDA",
    n_term=1,
    c_term=155,
    oligomeric_state=4,
)

# make sure to point to current path of the input data file
peptides = [
    Peptides(
        data_file=data_dir / "ecSecB_apo.csv",
        data_format=PeptideFormat.DynamX_v3_state,
        deuteration_type=DeuterationType.partially_deuterated,
        filters={
            "State": "SecB WT apo",
            "Exposure": [0.167, 0.5, 1.0, 10.0, 100.000008],
        },
        pH=8.0,
        temperature=303.15,
        d_percentage=90.0,
    ),
    Peptides(
        data_file=data_dir / "ecSecB_apo.csv",
        data_format=PeptideFormat.DynamX_v3_state,
        deuteration_type=DeuterationType.fully_deuterated,
        filters={
            "State": "Full deuteration control",
            "Exposure": 0.167,
        },
    ),
]

# %%
# test loading the peptides and verifying the sequence
# by comparing sequences of peptides to the protein state sequence
for peptide in peptides:
    verify_sequence(peptide.load(), protein_state.sequence, n_term=protein_state.n_term)

# %%
states = [
    State(
        name="Tetramer",
        description="SecB WT in tetrameric state",
        protein_state=protein_state,
        peptides=peptides,
    )
]

# %%

# state: dimer
protein_state = ProteinState(
    sequence="MSEQNNTEMTFQIQRIYTKDISFEAPNAPHVFQKDWQPEVKLDLDTASSQLADDVYEVVLRVTVTASLGEETAFLCEVQQGGIFSIAGIEGTQMAHCLGAYCPNILFPAARECIASMVARGTFPQLNLAPVNFDALFMNYLQQQAGEGTEEHQDA",
    n_term=1,
    c_term=155,
    oligomeric_state=2,
    mutations=[
        "Y109A",
        "T115A",
        "S119A",
    ],  # this information is also deducible by comparing sequences between states
)

peptides = [
    Peptides(
        data_file=data_dir / "ecSecB_dimer.csv",
        data_format=PeptideFormat.DynamX_v3_state,
        deuteration_type=DeuterationType.partially_deuterated,
        filters={
            "State": "SecB his dimer apo",
            "Exposure": [0.167, 0.5, 1.0, 10.0, 100.000008],
        },
        pH=8.0,
        temperature=303.15,
        d_percentage=90.0,
        chain=["A", "B"],  # specify chains for dimer
    )
]

# %%
# test loading the peptides and verifying the sequence
# by comparing sequences of peptides to the protein state sequence
for peptide in peptides:
    verify_sequence(peptide.load(), protein_state.sequence, n_term=protein_state.n_term)

# %%

states.append(
    State(
        name="Dimer",
        description="SecB mutatant in dimeric state",
        protein_state=protein_state,
        peptides=peptides,
    )
)

# %%
pub = Publication(
    title="Probing Universal Protein Dynamics Using Hydrogen-Deuterium Exchange Mass Spectrometry-Derived Residue-Level Gibbs Free Energy",
    doi="10.1021/acs.analchem.1c02155",
)

dataset = HDXDataSet(  # type: ignore[call-arg]
    states=states,
    description="HDX-MS dataset for SecB protein in tetramer/dimer states",
    structure=structure,
    protein_identifiers=protein_info,
    metadata=DatasetMetadata(  # type: ignore[call-arg]
        authors=[
            Author(
                name="Srinath Krishnamurthy", orcid="0000-0001-5492-4450", affiliation="KU Leuven"
            )
        ],
        publication=pub,
    ),
)

# %%
# submit the dataset to our database
success, msg_or_id = submit_dataset(dataset, database_dir)
if success:
    print(f"Dataset submitted successfully with ID: {msg_or_id}")
else:
    print(f"Failed to submit dataset: {msg_or_id}")

# %%
