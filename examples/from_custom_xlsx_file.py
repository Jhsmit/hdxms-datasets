"""
This is an example where the data source is an unsupported custom .xlsx file.
Since there are no supported converters for this format, we have to write a custom script
or manually convert to open HDX columns and then save as .csv.

Then, we define dataset metadata as normal and submit to a local database.

The data used in this example is available here:

https://pubs.acs.org/doi/suppl/10.1021/acs.analchem.2c01446/suppl_file/ac2c01446_si_002.xlsx
OR
https://acs.figshare.com/articles/dataset/Simple_and_Fast_Maximally_Deuterated_Control_maxD_Preparation_for_Hydrogen_Deuterium_Exchange_Mass_Spectrometry_Experiments/20260942

as part of the publication:
"Simple and Fast Maximally Deuterated Control (maxD) Preparation for Hydrogen-Deuterium Exchange Mass Spectrometry Experiments",


"""

# %%
from pathlib import Path

# optional biotite for parsing the structure and checking sequence
import biotite.database.rcsb as rcsb
import biotite.structure as struc
import biotite.structure.io as strucio
import polars as pl
from biotite.sequence import ProteinSequence
from fastexcel import read_excel

from hdxms_datasets.database import (
    submit_dataset,
)
from hdxms_datasets.models import (
    Author,
    DatasetMetadata,
    HDXDataSet,
    PeptideFormat,
    Peptides,
    ProteinIdentifiers,
    ProteinState,
    Publication,
    State,
    Structure,
)
from hdxms_datasets.view import StructureView

# %%
data_dir = Path(__file__).parent / "test_data" / "1_Mb"
data_dir.mkdir(parents=True, exist_ok=True)
excel_path = "ac2c01446_si_002.xlsx"

# the time points are given as text strings; we need to convert to seconds
time_map = {
    "1 min": 60.0,
    "10 min": 600.0,
    "30 min": 1800.0,
    "60 min": 3600.0,
    "120 min": 7200.0,
}

# %%
# read the data from the xlsx file, selecting the relevant sheet and columns/rows,
# then convert to polars. This selection includes partially deuterated data as well
# as fully deuterated (maxD) data.
reader = read_excel(data_dir / excel_path)
sheet = reader.load_sheet("Fig3", use_columns=list(range(0, 19)), n_rows=40, header_row=6)
df_raw = sheet.to_polars()

# %%
# define the columns with exposure and sequence
exposure_columns = df_raw.columns[6:11]

# first take the bottom-up uptake data and convert to open-hdxms format (names/dtype)
columns = [
    pl.col("Start").cast(pl.Int64).alias("start"),
    pl.col("End").cast(pl.Int64).alias("end"),
    pl.col("Peptide").alias("sequence"),
]
# %%
# the data here is a single replicate thus we don't have the uptake_sd column.
# this pipeline below takes the wide format data and pivots to long format
# and converts to open hdx format, and writes the files to the data directory
df = (
    df_raw[:, :11]
    .select(columns + exposure_columns)
    .unpivot(
        on=exposure_columns,
        index=["start", "end", "sequence"],
        variable_name="exposure",
        value_name="uptake",
    )
    .with_columns(
        [
            pl.col("exposure").replace(time_map).cast(pl.Float64).alias("exposure"),
            pl.lit("1_Mb").alias("state"),
        ]
    )
)
df.write_csv(data_dir / "1_Mb_peptides.csv")

# %%
# now take the fully deuterated data and convert to open-hdxms format
v1 = pl.col("MaxD Our protocol_1")
sd1 = pl.col("SD Our protocol_1")

v2 = pl.col("MaxD Our protocol_2")
sd2 = pl.col("SD Our protocol_2")

# this data set has two replicates, but each replicate is a triplicate
# we take the mean of the two replicates; error propagate sd
# write the file to the data directory
uptake = ((v1 + v2) / 2).alias("uptake")
uptake_sd = ((sd1**2 + sd2**2) ** 0.5 / 2).alias("uptake_sd")

df_fd = df_raw.select(columns + [uptake, uptake_sd])
df_fd.write_csv(data_dir / "1_Mb_fd_peptides.csv")

# %%

# In the second step, we define the metadata for this dataset and submit to a local database

# %%
cwd = Path(__file__).parent

# directory where to publish the dataset
database_dir = cwd / "published_datasets"
database_dir.mkdir(exist_ok=True)

time_map = {
    "1 min": 60.0,
    "10 min": 600.0,
    "30 min": 1800.0,
    "60 min": 3600.0,
    "120 min": 7200.0,
}


# %%

protein_info = ProteinIdentifiers(
    uniprot_accession_number="P68082",
    uniprot_entry_name="MYG_HORSE",
)


# %%
# fetch the structure from RCSB

try:
    rcsb.fetch("1AZI", "cif", data_dir / "1azi.cif")
except FileExistsError:
    pass

# %%
structure = Structure(
    data_file=data_dir / "1azi.cif",
    format="cif",
    description="MYOGLOBIN (HORSE HEART) RECOMBINANT WILD-TYPE COMPLEXED WITH AZIDE ",
    pdb_id="1AZI",
)

# define the sequence in this protein state
# residue numbers should match your HDX data
sequence = "GLSDGEWQQVLNVWGKVEADIAGHGQEVLIRLFTGHPETLEKFDKFKHLKTEAEMKASEDLKKHGTVVLTALGGILKKKGHHEAELKPLAQSHATKHKIPIKYLEFISDAIIHVLHSKHPGDFGADAQGAMTKALELFRNDIAAKYKELGFQG"
protein_state = ProteinState(
    sequence=sequence,
    n_term=1,
    c_term=len(sequence),
)

##

# lets verify the sequence defined in the protein state againts the structure sequence

atoms = strucio.load_structure(data_dir / "1azi.cif")
# select chain A and protein atoms only
atoms = atoms[atoms.chain_id == "A"]  # type: ignore
atoms = atoms[~atoms.hetero]  # type: ignore

resi, resn = struc.get_residues(atoms)
one_letter = "".join([ProteinSequence.convert_letter_3to1(r) for r in resn])

one_letter == protein_state.sequence  # type: ignore
# > True !
# note that here we assume both sequences start with n terminal residue with number 1
# if this is not the case, we need to do some extra work to align the sequences

# %%
# chain information is per peptide; such that multi-chain datasets can be defined
# if chain information is omitted, by default all chains are assumed to be the same
# (homomultimer or single chain)
# similarly, we can define multiple pH/temperature datasets here
pd_peptides = Peptides(  # type: ignore[call-arg]
    data_file=data_dir / "1_Mb_peptides.csv",
    data_format=PeptideFormat.OpenHDX,
    deuteration_type="partially_deuterated",
    pH=7.1,
    temperature=20 + 273.15,
    d_percentage=90.0,
)

fd_peptides = Peptides(  # type: ignore[call-arg]
    data_file=data_dir / "1_Mb_fd_peptides.csv",
    data_format=PeptideFormat.OpenHDX,
    deuteration_type="fully_deuterated",
    d_percentage=90.0,
)

# %%
# we can create a view of the structure and for example check peptide redundancy
StructureView(structure).peptide_redundancy(pd_peptides.load())

# %%
# This dataset has only one state, which is WT
state = State(
    name="1_Mb",
    peptides=[pd_peptides, fd_peptides],
    protein_state=protein_state,
)

# %%

pub = Publication(
    title="Simple and Fast Maximally Deuterated Control (maxD) Preparation for Hydrogen-Deuterium Exchange Mass Spectrometry Experiments",
    doi="10.1021/acs.analchem.2c01446",
    url="https://pubs.acs.org/doi/10.1021/acs.analchem.2c01446",
)

# Make sure to add the correct licsense for your dataset
# If you are the author, you can choose any license you like
# The preferred / default license is CC0

dataset = HDXDataSet(  # type: ignore[call-arg]
    states=[state],
    description="1 Mb dataset from Peterle et al. 2022",
    metadata=DatasetMetadata(  # type: ignore[call-arg]
        authors=[Author(name="Daniele Peterle", affiliation="Northeastern University")],
        publication=pub,
        license="CC BY-NC 4.0",
        conversion_notes="Converted published Supplementary data",
    ),
    protein_identifiers=protein_info,
    structure=structure,
)

# %%
# add the dataset to the database
# by default, the dataset is verified before submission
# this includes checking that specified protein sequences matches peptide sequences
success, msg_or_id = submit_dataset(dataset, database_dir, verify=True)


if success:
    print(f"Dataset submitted successfully with ID: {msg_or_id}")
else:
    print(f"Failed to submit dataset: {msg_or_id}")

# %%
