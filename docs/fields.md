# Fields

This document describes the fields used in open-hdxms files. The fields are divided into required, optional, and calculated fields.

Some fields can be both calculated from raw data (ie uptake) or provided directly

### start (int)
residue number of the first amino acid in the peptide

### end (int)
residue number of the last amino acid in the peptide

### sequence (str)
fasta sequence of the peptide

### protein (str)
protein name or identifier

HDExaminer name: Protein
DynamX name: Protein

### state (str)
state label

DynamX state/cluster name: State
HDExaminer name: Protein State
hxms name: PROTEIN_STATE

### replicate (str)
Label for the replicate
DynamX cluster name: File
HDExaminer name: Experiment

### exposure (float)
Deuterium exposure time in seconds

DynamX state/cluster name: Exposure
HDExaminer name: Deut Time

### centroid_mass (str)
calculated mass of uncharged peptide
derived from charge / centroid

### centroid_mass_sd (str)
Standard deviation of the centroid mass value

### centroid_mz

HDExaminer name: Exp Cent
DynamX name: ??

### centroid_mz_sd
Standard deviation of the centroid m/z value

### rt

retention time 
units unknown (minutes?)

DynamX state/cluster name: RT
HDExaminer name: Actual RT

### rt_sd (float)
Standard deviation of the retention time value

### charge (int)

DynamX cluster name: z
HDExaminer name: Charge

### intensity (float)

HDExaminer name: Max Inty
DynamX name?? is this max or mean intensity?

## Optional fields:
These fields can be present in open-hdxms files, but can also be calculated from the other fields.

### max_uptake (int)
Theoretical maximum deuterium uptake for the peptide. Equal to the number of 
non proline residues. Not that back-exchange is not considered here, including
back exchange of the N-terminal amide. 


### uptake (float)

Number of deuterium atoms incorporated into the peptide
calculated from centroid mass, if available

### uptake_sd (float)

Standard deviation of the uptake value


## Calculated fields:
These fields are derived from other fields defined in the above sections.

### n_replicates
added after data aggregation
Total number of replicates that were aggregated together

### n_charges
Total number of different charged states that were aggregated together

### n_clusters
added after data aggregation
Total number of isotopic clusters that were aggregated together. When replicates include multiple isotopic clusters (different charged states), this value will be larger than n_replicates.

### frac_fd_control (float)
Fractional deuterium uptake with respect to fully deuterated control sample

### frac_fd_control_sd (float)
Standard deviation of the fractional deuterium uptake with respect to fully deuterated control sample

### frac_max_uptake (float)
Fractional deuterium uptake with respect to the maximum possible uptake for the peptide

### frac_max_uptake_sd (float)
Standard deviation of the fractional deuterium uptake with respect to the maximum possible uptake for the peptide