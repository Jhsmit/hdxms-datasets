# HDXMS Datasets

Welcome to the HDXMS datasets repository. 

The `hdxms-datasets` package provides tools handling HDX-MS datasets.

The package offers the following features:

 - Defining datasets and their experimental metadata
 - Verification of datasets and metadata
 - Loading datasets from local or remote (WIP) database
 - Conversion of datasets from various formats (e.g., DynamX, HDExaminer) to a standardized format
 - Propagation of standard deviations from replicates to fractional relative uptake values

A database for open HDX datasets is set up at [HDXMS DataBase](https://github.com/Jhsmit/HDXMS-database)

## Example Usage

### Loading datasets


```python {title="Loading a dataset"}

from hdxms_datasets import DataBase

db = DataBase('path/to/local_db')
dataset = db.get_dataset('HDX_D9096080')

# Protein identifier information
print(dataset.protein_identifiers.uniprot_entry_name)
#> 'SECB_ECOLI'

# Access HDX states 
print([state.name for state in dataset.states])
#> ['Tetramer', 'Dimer']

# Get the sequence of the first state
state = dataset.states[0]
print(state.protein_state.sequence)
#> 'MSEQNNTEMTFQIQRIYT...'

# Load peptides
peptides = state.peptides[0]

# Access peptide information
print(peptides.deuteration_type, peptides.pH, peptides.temperature)
#> DeuterationType.partially_deuterated 8.0 303.15

# Load the peptide table as standardized narwhals DataFrame
df = peptides.load(
    convert=True,  # convert column header names to open hdx stanard
    aggregate=True, # aggregate centroids / uptake values across replicates
)

print(df.columns)
#> ['start', 'end', 'sequence', 'state', 'exposure', 'centroid_mz', 'rt', 'rt_sd', 'uptake', ... 

```

### Define and process datasets

```python {title="Define a set of peptides for a state"}
from hdxms_datasets import ProteinState, Peptides, verify_sequence, merge_peptides, compute_uptake_metrics

# Define the protein state
protein_state = ProteinState(
    sequence="MSEQNNTEMTFQIQRIYTKDISFEAPNAPHVFQKDWQPEVKLDLDTASSQLADDVYEVVLRVTVTASLGEETAFLCEVQQGGIFSIAGIEGTQMAHCLGAYCPNILFPYARECITSMVSRGTFPQLNLAPVNFDALFMNYLQQQAGEGTEEHQDA",
    n_term=1,
    c_term=155,
    oligomeric_state=4,
)

# Define the partially deuterated peptides for the SecB state
pd_peptides = Peptides(
    # path to the data file
    data_file=data_dir / "ecSecB_apo.csv",
    # specify the data format
    data_format=PeptideFormat.DynamX_v3_state,
    # specify the deuteration type (partially, fully or not deuterated)
    deuteration_type=DeuterationType.partially_deuterated,
    filters={
        "State": "SecB WT apo",
        # Optionally filter by exposure, leave out to include all exposures
        "Exposure": [0.167, 0.5, 1.0, 10.0, 100.000008],
    },
    # pH read without corrections
    pH=8.0,
    # temperature of the exchange buffer
    temperature=303.15,
    # deuterium percentage of the exchange buffer
    d_percentage=90.0,
)

# check for difference between the protein state sequence and the peptide sequences
mismatches = verify_sequence(pd_peptides.load(), protein_state.sequence, n_term=protein_state.n_term)
print(mismatches)
#> [] # sequences match

# Define the fully deuterated peptides for the SecB state
fd_peptides = Peptides(
    data_file=data_dir / "ecSecB_apo.csv",
    data_format=PeptideFormat.DynamX_v3_state,
    deuteration_type=DeuterationType.fully_deuterated,
    filters={
        "State": "Full deuteration control",
        "Exposure": 0.167,
    },
)

# merge both peptides together in a single dataframe
merged = merge_peptides([pd_peptides, fd_peptides])
print(merged.columns)
#> ['start', 'end', 'sequence', ... 'uptake', 'uptake_sd', 'fd_uptake', 'fd_uptake_sd']

# compute uptake metrics for the merged peptides
# this function computes uptake from centroid mass if not present
# as well as fractional uptake
processed = compute_uptake_metrics(merged)
print(processed.columns)
#> ['start', 'end', 'sequence', ... 'uptake', 'uptake_sd', 'fd_uptake', 'fd_uptake_sd', 'fractional_uptake', 'fractional_uptake_sd']

```

## Installation

```bash
$ pip install hdxms-datasets
```