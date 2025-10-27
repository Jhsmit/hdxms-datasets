# %%

from pathlib import Path
from typing import Optional

from hdxms_datasets.database import populate_known_ids, submit_dataset
from hdxms_datasets.loader import (
    read_hxms,
)
from hdxms_datasets.models import (
    Author,
    DatasetMetadata,
    DeuterationType,
    HDXDataSet,
    PeptideFormat,
    Peptides,
    ProteinIdentifiers,
    ProteinState,
    Publication,
    State,
    Structure,
    StructureMapping,
)
from hdxms_datasets.plot import plot_peptides
from hdxms_datasets.process import compute_uptake_metrics, merge_peptides
from hdxms_datasets.utils import (
    slice_exposure,
)
from hdxms_datasets.verification import compare_structure_peptides
from hdxms_datasets.view import StructureView

# %%

cwd = Path(__file__).parent
data_dir = cwd / "test_data" / "ecDHFR"

# directory where to publish the dataset
database_dir = cwd / "published_datasets"
database_dir.mkdir(exist_ok=True)

# %%
# define protein and structure
protein_info = ProteinIdentifiers(
    uniprot_accession_number="P0ABQ4",
    uniprot_entry_name="DYR_ECOLI",
)

structure = Structure(
    data_file=data_dir / "6XG5.cif",
    format="cif",
    pdb_id="6XG5",
    description="X-ray structure of Escherichia coli dihydrofolate reductase in complex with trimethoprim",
)


# %%
# define the states, one state per file
hxms_files = list(data_dir.glob("*.hxms"))
hxms_files
# %%
hxms_file = hxms_files[2]
hxms_file.stem.split("_")[-1]


# %%
def get_ligand(fpath: Path) -> Optional[str]:
    """
    Get ligand tag from filename.
    We assume that:
    MTX is metrotrexate
    TRI is trimethoprim (TMP)
    """
    tag = fpath.stem.split("_")[-1]
    if tag == "APO":
        return None
    elif tag == "MTX":
        return "metrotrexate"
    elif tag == "TRI":
        return "trimethoprim"
    return tag


get_ligand(hxms_file)

# %%

# structure mapping: chain A, residue offset -15 to match sequence numbering
mapping = StructureMapping(chain=["A"], residue_offset=-15)

# %%


# create a helper function to create a open-hdxms state object from the hdxms file
def make_state(hxms_file: Path) -> State:
    hxms_result = read_hxms(hxms_file)
    sequence = hxms_result["METADATA"]["PROTEIN_SEQUENCE"]

    ligand = get_ligand(hxms_file)
    name = f"ec_DHFR_{'WT' if ligand is None else ligand}"

    protein_state = ProteinState(
        sequence=sequence,
        n_term=1,
        c_term=len(sequence),
        ligand=ligand,
    )

    # get the peptide metadata from read peptides
    pd_peptide_metadata = {
        "temperature": hxms_result["METADATA"]["TEMPERATURE(K)"],
        "pH": hxms_result["METADATA"]["pH(READ)"],
        "d_percentage": float(hxms_result["METADATA"]["D2O_SATURATION"]) * 100,
    }

    # get the partially deuterated timepoints
    assert "DATA" in hxms_result
    df = hxms_result["DATA"]
    all_timepoints = df["TIME(Sec)"].unique().to_list()
    pd_timepoints = sorted(set(all_timepoints) - {0.0, float("inf")})

    peptides = [
        Peptides(
            data_file=hxms_file,
            data_format=PeptideFormat.HXMS,
            deuteration_type=DeuterationType.partially_deuterated,
            filters={
                "TIME(Sec)": pd_timepoints,
            },
            structure_mapping=mapping,
            **pd_peptide_metadata,
        )
    ]

    # add nondeuterated and fully deuterated peptides
    # note that nondeuterated peptides have zero uptake values
    # and thus contain no information in this case
    # list of (type, value):
    other_peptides = [
        (DeuterationType.non_deuterated, 0.0),
        (DeuterationType.fully_deuterated, float("inf")),
    ]

    for deuteration_type, timepoint in other_peptides:
        if timepoint in all_timepoints:
            peptides.append(
                Peptides(
                    data_file=hxms_file,
                    data_format=PeptideFormat.HXMS,
                    deuteration_type=deuteration_type,
                    filters={
                        "TIME(Sec)": timepoint,
                    },
                ),
            )

    state = State(
        name=name,
        description=f"E. coli DHFR {'wild-type' if ligand is None else f'in complex with {ligand}'}",
        protein_state=protein_state,
        peptides=peptides,
    )

    return state


# create the states
states = [make_state(fpath) for fpath in hxms_files]

# %%

pub = Publication(
    title="HXMS: a standardized file format for HX/MS data",
    doi="10.1101/2025.10.14.682397 ",  # not that the DOI in the files refer to the PIGEON-FEATHER MS
)

metadata = DatasetMetadata(  # type: ignore[call-arg]
    authors=[
        Author(
            name="Andrew Reckers",
            orcid="0000-0002-7567-8540",
            affiliation="Department of Biochemistry and Molecular Biophysics, Columbia University Irving Medical Center, New York, NY, United States",
        )
    ],
    publication=pub,
    license="CC BY 4.0",
)

dataset = HDXDataSet(  # type: ignore[call-arg]
    states=states,
    description="HDX-MS dataset for E. coli dihydrofolate reductase in apo and inhibitor-bound forms",
    structure=structure,
    protein_identifiers=protein_info,
    metadata=metadata,
)

# %%
# load the peptides from the first state
peptides = dataset.states[0].peptides[0]
df = peptides.load()
# %%

# check to see if peptides match the supplied structure by amino acid identity
compare_structure_peptides(structure, peptides)
# > {'total_residues': 165, 'matched_residues': 159, 'identical_residues': 157}

# %%
# view coverage of peptides on the structure
view = StructureView(structure, mapping=peptides.structure_mapping).color_peptide(start=11, end=19)
view

# %%
# view peptide redundancy
view = StructureView(structure, mapping=peptides.structure_mapping).peptide_redundancy(df)
view

# %%

merged = merge_peptides(dataset.states[1].peptides)

# compute uptake metrics (uptake, fractional deuterium), view result in peptide plot
processed = compute_uptake_metrics(merged).to_polars()

df_exposure = slice_exposure(processed)[5]
plot_peptides(df_exposure, value="frac_max_uptake").interactive()

# %%
populate_known_ids(database_dir)

success, msg_or_id = submit_dataset(dataset, database_dir, allow_mint_new_id=True)
if success:
    print(f"Dataset submitted successfully with ID: {msg_or_id}")
else:
    print(f"Failed to submit dataset: {msg_or_id}")
