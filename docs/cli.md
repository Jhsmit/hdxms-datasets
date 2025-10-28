# Command Line Interface (CLI)

The `hdxms-datasets` package provides a command-line interface to help you create and manage HDX-MS datasets.

## Installation

First, install the package with the CLI dependencies:

```bash
pip install -e .
```

After installation, the `hdxms-datasets` command will be available in your terminal.

## Commands

### `hdxms-datasets create`

Create a new HDX-MS dataset with a unique ID and template script.

**Basic usage:**

```bash
hdxms-datasets create
```

This will:
1. Generate a unique HDX dataset ID (e.g., `HDX_A1B2C3D4`)
2. Create a new directory in the current directory: `<HDX_ID>/`
3. Generate a template `create_dataset.py` script with configuration
4. Create a `data/` subdirectory for your raw data files
5. Generate a `README.md` with quick start instructions

**Options:**

- `--num-states, -n INTEGER`: Number of protein states (default: 1)
- `--format, -f CHOICE`: Data format - OpenHDX, DynamX_v3_state, DynamX_v3_cluster, HDExaminer (default: OpenHDX)
- `--ph FLOAT`: Experimental pH (default: 7.5)
- `--temperature, -t FLOAT`: Temperature in Kelvin (default: 293.15)
- `--database-dir, -d PATH`: Path to existing database directory to check for ID conflicts
- `--help`: Show help message

**Examples:**

```bash
# Create with defaults (OpenHDX, 1 state, pH 7.5, 20°C)
hdxms-datasets create

# Create with custom parameters
hdxms-datasets create --num-states 2 --format DynamX_v3_state --ph 8.0 --temperature 298.15

# Using short flags
hdxms-datasets create -n 3 -f HDExaminer --ph 7.0 -t 293.15

# Check for ID conflicts with existing database
hdxms-datasets create --database-dir ~/hdx-database/datasets
```

## Configuration via Arguments

All dataset configuration is specified via command-line arguments:

- **Number of states** (`--num-states`): How many different protein states you measured (default: 1)
- **Data format** (`--format`): Which software generated your data (default: OpenHDX)
  - `OpenHDX` - OpenHDX format
  - `DynamX_v3_state` - DynamX state files
  - `DynamX_v3_cluster` - DynamX cluster files  
  - `HDExaminer` - HDExaminer files
- **pH** (`--ph`): Experimental pH value (default: 7.5)
- **Temperature** (`--temperature`): Temperature in Kelvin (default: 293.15 K = 20°C)

## Workflow Example

```bash
# Step 1: Create a new dataset with custom parameters
$ hdxms-datasets create --num-states 2 --format DynamX_v3_state --ph 8.0

✓ Generated new dataset ID: HDX_A1B2C3D4
============================================================
✓ Dataset template created successfully!
============================================================

Dataset ID:     HDX_A1B2C3D4
Location:       C:\Users\username\HDX_A1B2C3D4
Format:         DynamX_v3_state
States:         2
pH:             8.0
Temperature:    293.15 K (20.0°C)

Next steps:
  1. cd HDX_A1B2C3D4
  2. Place your data files in the data/ directory
  3. Edit create_dataset.py with your specific information
  4. python create_dataset.py

# Step 2: Navigate to the new directory
$ cd HDX_A1B2C3D4

# Step 3: Copy your data files
$ copy C:\path\to\my\data.csv data\

# Step 4: Edit the template script
$ notepad create_dataset.py
# Edit the file with your specific information:
#   - Replace protein sequences
#   - Update data file names
#   - Add author information
#   - Add publication details

# Step 5: Run the script to create your dataset
$ python create_dataset.py
✓ Dataset submitted successfully with ID: HDX_A1B2C3D4
  Dataset location: C:\Users\username\HDX_A1B2C3D4\dataset\HDX_A1B2C3D4
```

## Generated Template Structure

After running `hdxms-datasets create`, you'll have:

```
HDX_A1B2C3D4/
├── create_dataset.py    # Template script to edit
├── README.md            # Quick start guide
└── data/                # Directory for your raw data files
```

The `create_dataset.py` template includes:
- Clearly marked sections to edit
- Inline comments explaining each field
- List-based structure for protein states and peptides (flexible and easy to extend)
- Pre-configured pH and temperature values from your command-line arguments
- Example values to guide you
- Automatic sequence verification
- Dataset submission code

Please note that this template is not exhaustive and other metadata fields may be used 
depending on your dataset's requirements. 

## Future Commands (Planned)

The CLI is designed to be extensible. Future commands may include:

- `hdxms-datasets validate`: Validate a dataset before submission
- `hdxms-datasets upload`: Upload a dataset to a remote database
- `hdxms-datasets export`: Export a dataset to different formats

## Getting Help

For more information about any command:

```bash
hdxms-datasets --help
hdxms-datasets create --help
```
