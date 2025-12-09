# HD examiner export format

There are multiple different file format formats of HD Examiner exported HDX-MS data published. This page provides an overview of the different formats in an attempt to assign HD examiner version numbers and export name / functionality to the different formats.

See docs/hd_examiner_files for a collection of example files. 

### HDgraphiX pool output

File: 'HDgraphiX Sample HDExaminer Pool.csv'
Source: [HDGraphix](https://hdgraphix.net/).

Columns:
The first line is a header with exposure times. 

The second line has the column names, starting with:
'State,Protein,Start,End,Sequence,Search RT,Charge,Max D,'

Followed by repeating blocks of:
'Start RT,End RT,#D,%D,#D right,%D right,Score,Conf,'

FD control is expected to be labelled as 'Full-D'

Comments:
Data itself has alternating empty lines?

Reading: [GitHub](https://github.com/KentV-UofG/HDgraphiX/blob/d68b1c941acf85c6d4429dfcee85b2c3420ba221/app.py#L614)

### HDgraphiX summary output

File: 'HDgraphiX Sample HDExaminer Summary.csv'
Source: [HDGraphix](https://hdgraphix.net/).

Columns:
Protein State,Protein,Start,End,Sequence,Peptide Mass,RT (min),Deut Time (sec),maxD,Theor Uptake,#D,%D,Conf Interval (#D),#Rep,Confidence,Stddev,p

Format: HDgraphiX Summary

Comments:
Data itself has alternating empty lines?

### PFLink example file 'pool peptide results'

File: ecDHFR_tutorial.csv
Source: https://huggingface.co/spaces/glasgow-lab/PFLink

Columns: 
Same as HDgrapix pool output

Format: HD examiner peptide pool / HD examiner pool

Comments:
This is similar to HDgraphix pool output, no alternating empty lines.
FD control exposure is labelled as 'Full-D'

Reading: [Huggingface code](https://huggingface.co/spaces/glasgow-lab/PFLink/blob/main/Parsers.py#L278)

### HD Examiner v3.4 export

File: < Not public >
Source: Data provided by Vladimir Sarpe from Trajan (not public)

Columns:
'Protein State,Deut Time,Experiment,Start,End,Sequence,Charge,Search RT,Actual RT,# Spectra,Peak Width Da,m/z Shift Da,Max Inty,Exp Cent,Theor Cent,Score,Cent Diff,# Deut,Deut %,Confidence'

'Deut Time' columns are in seconds, stored as strings formatted as '0s'. FD control is labelled as 'FD' in this columns. 

Format: HD examiner V3.4 (as currently used in `hdxms-datasets`)

Comments:
Unknown name of export function used in HD Examiner v3.4


### Tang et al HD examiner export

File: 'Tang_HDExaminer_layout_SLO.csv'
Source: https://www.ebi.ac.uk/pride/archive/projects/PXD047461


columns: 
Protein;Protein State;Deut Time;Experiment;Start;End;Sequence;Charge;Search RT;Actual RT;# Spectra;Peak Width;m/z Shift;Max Inty;Exp Cent;Exp Cent 2;L/R Ratio;Theor Cent;Theor Cent 2;Theor L/R;Score;Cent Diff;# Deut;Deut %;Cent Diff 2;# Deut 2;Deut % 2;Confidence

Comments:
This is a ; separated file

### Ekström et al HD examiner export

File: 'HDX_S3.csv'
Source: https://www.ebi.ac.uk/pride/archive/projects/PXD021266

Columns: Protein State,Protein,Start,End,Sequence,Peptide Mass,RT (min),Deut Time (sec),maxD,Theor #D,#D,%D,Conf Interval (#D),#Rep,Confidence,Stddev,p

Format: HD examiner summary file

### Burke et al HD examiner export

File: 'adjusted_ND_peptides.csv'
Source: https://www.ebi.ac.uk/pride/archive/projects/PXD022172

Columns: Start,End,Sequence,Charge,Search RT,Actual RT,# Spectra,Peak Width,m/z Shift,Max Inty,Exp Cent,Theor Cent,Score,Confidence

Format: Unkown

Looks like HD examiner but doesnt match previously seen columns


### Bryan et al HD examiner export

File: 2020_ISB_Droplet_HXMS_Experiment_Data_Reduction_All_Results_Table_20220603.csv
Source: https://www.ebi.ac.uk/pride/archive/projects/PXD034374

Columns: Protein State,Deut Time,Experiment,Start,End,Sequence,Charge,Search RT,Actual RT,# Spectra,Peak Width,m/z Shift,Max Inty,Exp Cent,Theor Cent,Score,Cent Diff,# Deut,Deut %,Confidence

Format: Unkown

Looks like HD examiner but doesnt match previously seen columns
