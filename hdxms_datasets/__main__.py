"""
Command-line interface for hdxms-datasets package.
"""

from __future__ import annotations

from pathlib import Path
import typer
from enum import Enum

from hdxms_datasets.database import mint_new_dataset_id, populate_known_ids

app = typer.Typer(
    name="hdxms-datasets",
    help="Tools for creating and managing HDX-MS datasets",
    add_completion=False,
    no_args_is_help=True,
)


class DataFormat(str, Enum):
    """Supported HDX-MS data formats."""

    openhdx = "OpenHDX"
    dynamx_v3_state = "DynamX_v3_state"
    dynamx_v3_cluster = "DynamX_v3_cluster"
    hdexaminer = "HDExaminer"


def generate_template_script(
    dataset_id: str,
    data_format: DataFormat,
    num_states: int = 1,
    ph: float = 7.5,
    temperature: float = 293.15,
) -> str:
    """Generate a minimal create_dataset.py script based on user choices."""

    # Build state creation code - keep as list for flexibility
    states_code_lines = []
    for i in range(num_states):
        state_num = i + 1
        states_code_lines.append(f"""    # State {state_num}
    ProteinState(
        sequence="MSEQNNTEMTFQIQRIYTKDISFEAPNAPHVFQKDWQPEVKLDLDTASSQLADDVYEVVLRVTVTASLGEETAFLCEVQQGGIFSIAGIEGTQMAHCLGAYCPNILFPYARECITSMVSRGTFPQLNLAPVNFDALFMNYLQQQAGEGTEEHQDA",  # Replace with your protein sequence
        n_term=1,  # N-terminal residue number
        c_term=155,  # C-terminal residue number
        oligomeric_state=1,  # Monomer=1, Dimer=2, etc.
        mutations=None, # Add mutations as a list of strings if applicable
        ligand=None,  # Add ligand information if applicable
    ),""")

    protein_states_list = "\n".join(states_code_lines)

    # Build peptide list items
    peptides_list_items = []
    for i in range(num_states):
        state_num = i + 1
        peptides_list_items.append(f"""    [
        # Peptides for state {state_num}
        Peptides(
            data_file=data_dir / "your_data_file.csv",  # Replace with your data file name
            data_format=PeptideFormat.{data_format.value},
            deuteration_type=DeuterationType.partially_deuterated,
            filters={{}},  # Add filters as needed, e.g. {{"State": "WT", "Exposure": [0.5, 1.0, 10.0]}}
            pH={ph},  # pH as read with the pH meter
            temperature={temperature}, # Temperature in Kelvin
            d_percentage=90.0,  # Deuterium percentage
            structure_mapping=mapping  # Adjust chain and offset as needed
        ),
        Peptides(
            data_file=data_dir / "your_data_file.csv",  # Replace with your data file name
            data_format=PeptideFormat.{data_format.value},
            deuteration_type=DeuterationType.fully_deuterated,
            filters={{}},  # Add filters as needed, e.g. {{"State": "Fully Deuterated", "Exposure": "0.167"}}
            d_percentage=90.0,  # Deuterium percentage
            structure_mapping=mapping
        ),
    ],""")

    peptides_list = "\n".join(peptides_list_items)

    # Build state names list
    state_names_list = ",\n    ".join([f'"State_{i + 1}"' for i in range(num_states)])

    template = f'''"""
Dataset creation script for {dataset_id}

This script defines an HDX-MS dataset and submits it to a local database.
Edit the marked sections below with your specific data.
"""

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
    StructureMapping,
)
from hdxms_datasets.utils import verify_sequence

# =============================================================================
# SETUP: Define your directories
# =============================================================================
cwd = Path(__file__).parent

# Directory containing your raw data files
data_dir = cwd / "data"

# Directory where the dataset will be published (parent/<HDX_ID>/dataset)
database_dir = cwd.parent / "dataset"
database_dir.mkdir(exist_ok=True)

# =============================================================================
# PROTEIN INFORMATION: Define your protein
# =============================================================================
protein_info = ProteinIdentifiers(
    uniprot_accession_number=None,  # Replace with your UniProt accession
    uniprot_entry_name=None,  # Replace with your UniProt entry name
)

# Add structural information
structure = Structure(
    data_file=data_dir / "structure.cif",  # Path to your structure file
    format="cif",  # or "pdb"
    pdb_id="",  # Replace with your PDB ID if applicable
    description="",  # Add optional description
)

# Optional structural mapping used to related peptides to the structure
mapping = StructureMapping(chain=["A"], residue_offset=0)  # Adjust chain and offset as needed

# =============================================================================
# STATES: Define your protein states
# =============================================================================

# List of protein states - edit each state's properties
protein_states = [
{protein_states_list}
]

# List of peptide groups corresponding to each state
# Each inner list contains Peptides objects for that state
# Filters can be used to select the relevant rows from your data file
# Leave empty to select all rows. 
all_peptides = [
{peptides_list}
]

# State names and descriptions
state_names = [
    {state_names_list}
]

state_descriptions = [
    "Description of state {{i+1}}" for i in range(len(protein_states))
]

# Verify sequences and build State objects
states = []
for i, (prot_state, peptides_group, name, desc) in enumerate(
    zip(protein_states, all_peptides, state_names, state_descriptions)
):
    # Verify each peptide's sequence
    for peptide in peptides_group:
        verify_sequence(peptide.load(), prot_state.sequence, n_term=prot_state.n_term)
    
    # Create State object
    states.append(
        State(
            name=name,
            description=desc,
            protein_state=prot_state,
            peptides=peptides_group,
        )
    )

# =============================================================================
# METADATA: Publication and author information
# =============================================================================
pub = Publication(
    title="Your publication title",
    doi="10.xxxx/xxxxx",  # Replace with your DOI
    year=2024,
)

# =============================================================================
# CREATE DATASET: Assemble all components
# =============================================================================
dataset = HDXDataSet(  # type: ignore[call-arg]
    hdx_id="{dataset_id}",
    states=states,
    description="Brief description of your HDX-MS dataset",
    structure=structure,
    protein_identifiers=protein_info,
    metadata=DatasetMetadata(  # type: ignore[call-arg]
        authors=[
            Author(
                name="Your Name",
                orcid="0000-0000-0000-0000",  # Your ORCID (optional)
                affiliation="Your Institution",
            )
        ],
        license="CC BY 4.0",  # Choose appropriate license
        publication=pub,
    ),
)

# =============================================================================
# SUBMIT: Save the dataset to the database
# =============================================================================
success, msg_or_id = submit_dataset(dataset, database_dir, allow_mint_new_id=False)
if success:
    print(f"✓ Dataset submitted successfully with ID: {{msg_or_id}}")
    print(f"  Dataset location: {{database_dir / msg_or_id}}")
else:
    print(f"✗ Failed to submit dataset: {{msg_or_id}}")
'''
    return template


@app.callback()
def callback():
    pass


@app.command(name="create")
def create(
    num_states: int = typer.Option(
        1,
        "--num-states",
        "-n",
        help="Number of protein states to include in the dataset",
    ),
    data_format: DataFormat = typer.Option(
        DataFormat.openhdx,
        "--format",
        "-f",
        help="Data format for HDX-MS files",
    ),
    ph: float = typer.Option(
        7.5,
        "--ph",
        help="Experimental pH",
    ),
    temperature: float = typer.Option(
        293.15,
        "--temperature",
        "-t",
        help="Experimental temperature in Kelvin (default: 293.15 K = 20°C)",
    ),
    database_dir: Path = typer.Option(
        None,
        "--database-dir",
        "-d",
        help="Path to existing database directory to check for ID conflicts",
    ),
):
    """
    Create a new HDX-MS dataset with a unique ID and template script.

    This command will:
    1. Generate a unique HDX dataset ID
    2. Create a new directory: <HDX_ID>/dataset
    3. Generate a template Python script to help you create your dataset

    After running this command, edit the generated create_dataset.py script
    with your specific data and metadata.

    Example:
        hdxms-datasets create
        hdxms-datasets create --num-states 2 --format DynamX_v3_state --ph 8.0
    """

    # Load existing IDs if database directory provided
    if database_dir is not None:
        database_dir = database_dir.resolve()
        if database_dir.exists():
            typer.echo(f"📂 Checking existing IDs in: {database_dir}")
            populate_known_ids(database_dir)
        else:
            typer.echo(f"⚠️  Database directory not found: {database_dir}")
            typer.echo("   Continuing without conflict checking...")

    # Mint new dataset ID
    dataset_id = mint_new_dataset_id()
    typer.echo(
        f"\n✓ Generated new dataset ID: {typer.style(dataset_id, fg=typer.colors.GREEN, bold=True)}"
    )

    # Create dataset directory structure: <HDX_ID>/dataset
    output_dir = Path.cwd()
    dataset_dir = output_dir / dataset_id

    if dataset_dir.exists():
        typer.echo(f"\n⚠️  Directory already exists: {dataset_dir}")
        if not typer.confirm("   Overwrite?"):
            typer.echo("Aborted.")
            raise typer.Exit(1)

    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Create data subdirectory
    data_dir = dataset_dir / "data"
    data_dir.mkdir(exist_ok=True)

    # Generate and write template script
    script_content = generate_template_script(
        dataset_id=dataset_id,
        data_format=data_format,
        num_states=num_states,
        ph=ph,
        temperature=temperature,
    )

    script_path = dataset_dir / "create_dataset.py"
    script_path.write_text(script_content, encoding="utf-8")

    # Create a README
    readme_content = f"""# HDX-MS Dataset: {dataset_id}

## Quick Start

1. Place your HDX-MS data files in the `data/` directory
2. Edit `create_dataset.py` and fill in:
   - Your protein structure information
   - Your protein state metadata
   - Your HDX peptides for each state
   - Author information
   - Publication details
3. Run the script: `python create_dataset.py`

## Dataset Configuration

- **Format**: {data_format.value}
- **Number of states**: {num_states}
- **pH**: {ph}
- **Temperature**: {temperature} K ({temperature - 273.15:.1f}°C)

## Directory Structure

```
{dataset_id}/
├── create_dataset.py    # Template script to edit
├── README.md            # This file
├── data/                # Place your raw data files here
└── dataset/             # Will be created when you run create_dataset.py
```

## Next Steps

Review the template script and customize it for your dataset.
The template uses lists for protein states and peptides to maintain flexibility.

See the hdxms-datasets documentation for more details:
https://jhsmit.github.io/hdxms-datasets/
"""

    readme_path = dataset_dir / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")

    # Success message
    typer.echo("\n" + "=" * 60)
    typer.echo(
        typer.style("✓ Dataset template created successfully!", fg=typer.colors.GREEN, bold=True)
    )
    typer.echo("=" * 60)
    typer.echo(f"\nDataset ID:     {dataset_id}")
    typer.echo(f"Location:       {dataset_dir}")
    typer.echo(f"Format:         {data_format.value}")
    typer.echo(f"States:         {num_states}")
    typer.echo(f"pH:             {ph}")
    typer.echo(f"Temperature:    {temperature} K ({temperature - 273.15:.1f}°C)")
    typer.echo("\nNext steps:")
    typer.echo(f"  1. cd {dataset_dir}")
    typer.echo("  2. Place your data files in the data/ directory")
    typer.echo("  3. Edit create_dataset.py with your specific information")
    typer.echo("  4. python create_dataset.py")
    typer.echo()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
