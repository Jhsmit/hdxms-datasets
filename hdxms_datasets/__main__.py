"""
Command-line interface for hdxms-datasets package.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
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
    d_percentage: float = 90.0,
) -> str:
    """Generate a minimal create_dataset.py script based on user choices."""

    # Build state creation code - directly append State objects
    states_code_lines = []
    for i in range(num_states):
        state_num = i + 1
        states_code_lines.append(f"""
states.append(
    State(
        name="State_{state_num}",  # update with your state name - should a short human readable descriptor
        description="",  # Optional state description
        protein_state=ProteinState(
            sequence="MSEQNNTEMTFQIQRIYTKDISFEAPNAPHVFQKDWQPEVKLDLDTASSQLADDVYEVVLRVTVTASLGEETAFLCEVQQGGIFSIAGIEGTQMAHCLGAYCPNILFPYARECITSMVSRGTFPQLNLAPVNFDALFMNYLQQQAGEGTEEHQDA",  # Replace with your protein sequence
            n_term=1,  # N-terminal residue number
            c_term=155,  # C-terminal residue number
            oligomeric_state=1,  # Monomer=1, Dimer=2, etc.
            mutations=None,  # Add mutations as a list of strings if applicable
            ligand=None,  # Add ligand information if applicable
        ),
        peptides=[
            # Peptides for state {state_num}
            Peptides(
                data_file=data_dir / "your_data_file.csv",  # Replace with your data file name
                data_format=PeptideFormat.{data_format.value},
                deuteration_type=DeuterationType.partially_deuterated,
                filters={{}},  # Add filters as needed, e.g. {{"State": "WT", "Exposure": [0.5, 1.0, 10.0]}}
                pH={ph},  # pH as read with the pH meter
                temperature={temperature},  # Temperature in Kelvin
                d_percentage={d_percentage},  # Deuterium percentage
                structure_mapping=mapping,  # Adjust chain and offset as needed
            ),
            Peptides(
                data_file=data_dir / "your_data_file.csv",  # Replace with your data file name
                data_format=PeptideFormat.{data_format.value},
                deuteration_type=DeuterationType.fully_deuterated,
                filters={{}},  # Add filters as needed, e.g. {{"State": "Fully Deuterated", "Exposure": "0.167"}}
                d_percentage={d_percentage},  # Deuterium percentage
                structure_mapping=mapping,
            ),
            Peptides(
                data_file=data_dir / "your_data_file.csv",  # Replace with your data file name
                data_format=PeptideFormat.{data_format.value},
                deuteration_type=DeuterationType.non_deuterated,
                filters={{}},  # Add filters as needed, e.g. {{"State": "WT", "Exposure": "0"}}
                structure_mapping=mapping,
            ),
        ],
    )
)""")

    states_blocks = "\n".join(states_code_lines)

    template = f'''"""
Dataset creation script for {dataset_id}

This script defines an HDX-MS dataset and submits it to a local database.
Edit the marked sections below with your specific data.
"""

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

# =============================================================================
# SETUP: Define your directories
# =============================================================================
cwd = Path(__file__).parent

# Directory containing your raw data files
data_dir = cwd / "data"

# Directory where the dataset will be published
database_dir = cwd / "output"
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

# This section defines the protein states and which peptides belong to the state
# Add or remove peptide types as needed. The format supports multiple peptides of the same type
# for example for multi pH/temperature datasets.
# Filters can be used to select the relevant rows from your data file
# Leave empty to select all rows.

states = []
{states_blocks}


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
    print(f"✓ Dataset created successfully with ID: {{msg_or_id}}")
    print(f"  Dataset location: {{database_dir / msg_or_id}}")
    print("Create a pull request with your dataset to contribute it to the public database.")
else:
    print(f"✗ Failed to submit dataset: {{msg_or_id}}")
'''
    return template


@app.callback()
def callback():
    pass


@app.command(name="create")
def create(
    short_name: str = typer.Option(
        None,
        "--short-name",
        "-s",
        help="Optional short name to append to the timestamp folder name. Suggested name is 'authorname_proteinname'",
    ),
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
    d_percentage: float = typer.Option(
        90.0,
        "--d-percentage",
        "-dperc",
        help="Deuterium percentage of the labeling solution (default: 90.0)",
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
    2. Create a new timestamped directory: YYYYMMDD_HHMM_HDX_ID_short_name (or YYYYMMDD_HHMM_HDX_ID if no short name)
    3. Generate a template Python script to help you create your dataset

    After running this command, edit the generated create_dataset.py script
    with your specific data and metadata.

    Example:
        hdxms-datasets create
        hdxms-datasets create --short-name secb_wt
        hdxms-datasets create --num-states 2 --format DynamX_v3_state --ph 8.0 --short-name my_protein
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

    # Create timestamped folder name with dataset ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    if short_name:
        folder_name = f"{timestamp}_{dataset_id}_{short_name}"
    else:
        folder_name = f"{timestamp}_{dataset_id}"

    # Create dataset directory structure: <timestamp_folder>/
    output_dir = Path.cwd()
    dataset_dir = output_dir / folder_name

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
        d_percentage=d_percentage,
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

- **Dataset ID**: {dataset_id}
- **Folder**: {folder_name}
- **Format**: {data_format.value}
- **Number of states**: {num_states}
- **pH**: {ph}
- **Temperature**: {temperature} K ({temperature - 273.15:.1f}°C)

## Directory Structure

```
{folder_name}/
├── create_dataset.py    # Template script to edit
├── README.md            # This file
├── data/                # Place your raw data files here
└── output/              # Will be created when you run create_dataset.py
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
    typer.echo(f"Folder:         {folder_name}")
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
