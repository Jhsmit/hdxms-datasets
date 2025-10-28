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
2. Create a new directory with the dataset ID
3. Generate a template `create_dataset.py` script
4. Create a `data/` subdirectory for your raw data files
5. Generate a `README.md` with quick start instructions

**Options:**

- `--output-dir, -o PATH`: Specify where to create the dataset folder (default: current directory)
- `--database-dir, -d PATH`: Path to existing database directory to check for ID conflicts
- `--help`: Show help message

**Examples:**

```bash
# Create in current directory
hdxms-datasets create

# Create in specific directory
hdxms-datasets create --output-dir ~/my-hdx-datasets

# Check for ID conflicts with existing database
hdxms-datasets create --database-dir ~/hdx-database/datasets
```

## Interactive Prompts

When you run `hdxms-datasets create`, you'll be asked:

1. **Number of protein states**: How many different states you measured (default: 1)
2. **Data format**: Which software generated your data:
   - DynamX_v3_state
   - DynamX_v3_cluster
   - HDExaminer
   - OpenHDX
3. **License**: Which license to apply to your dataset:
   - CC BY 4.0 (recommended for open data)
   - CC BY-SA 4.0
   - CC BY-NC 4.0
   - CC0 1.0
   - MIT

## Workflow Example

```bash
# Step 1: Create a new dataset
$ hdxms-datasets create

✓ Generated new dataset ID: HDX_A1B2C3D4

============================================================
Dataset Configuration
============================================================

How many protein states will you measure? [1]: 2

Available data formats:
  1. DynamX_v3_state
  2. DynamX_v3_cluster
  3. HDExaminer
  4. OpenHDX

Select your data format [DynamX_v3_state]: DynamX_v3_state

Available licenses:
  1. CC BY 4.0
  2. CC BY-SA 4.0
  3. CC BY-NC 4.0
  4. CC0 1.0
  5. MIT

Select a license for your dataset [CC BY 4.0]: CC BY 4.0

============================================================
✓ Dataset template created successfully!
============================================================

Dataset ID:  HDX_A1B2C3D4
Location:    C:\Users\username\HDX_A1B2C3D4

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
# (Edit the file with your specific information)

# Step 5: Run the script to create your dataset
$ python create_dataset.py
✓ Dataset submitted successfully with ID: HDX_A1B2C3D4
  Dataset location: C:\Users\username\published_datasets\HDX_A1B2C3D4
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
- Example values based on your configuration choices
- Automatic sequence verification
- Dataset submission code

## Future Commands (Planned)

The CLI is designed to be extensible. Future commands may include:

- `hdxms-datasets validate`: Validate a dataset before submission
- `hdxms-datasets upload`: Upload a dataset to a remote database
- `hdxms-datasets list`: List datasets in a database
- `hdxms-datasets export`: Export a dataset to different formats

## Getting Help

For more information about any command:

```bash
hdxms-datasets --help
hdxms-datasets create --help
```

For package documentation:
- [Main documentation](https://jhsmit.github.io/hdxms-datasets/)
- [GitHub repository](https://github.com/Jhsmit/hdxms-datasets/)
