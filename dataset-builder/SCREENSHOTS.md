# HDX-MS Dataset Builder - Visual Guide

This document describes what you'll see when using the application.

## Application Flow

### 1. Step 1: File Upload
**What you'll see:**
- A clean header with the application title
- Progress bar showing 6 steps (Step 1 highlighted)
- Two upload sections:
  - "Data Files" - for CSV files
  - "Structure File" - for PDB/mmCIF files
- Drag-and-drop areas or "Browse Files" buttons
- List of uploaded files with:
  - Filename
  - File size
  - Detected format badge (for data files)
  - Remove button

**What to do:**
- Upload your CSV data files
- Upload your structure file (PDB or mmCIF)
- Click "Next" when done

---

### 2. Step 2: Protein Information
**What you'll see:**
- Progress bar (Step 2 highlighted)
- Three input fields:
  - UniProt Accession Number
  - UniProt Entry Name
  - Protein Name
- All fields are optional

**What to do:**
- Enter protein identifiers if available
- Click "Next" to continue

---

### 3. Step 3: Structure Configuration
**What you'll see:**
- Progress bar (Step 3 highlighted)
- Dropdown to select uploaded structure file
- Format dropdown (PDB, mmCIF, BinaryCIF)
- Optional fields:
  - PDB ID
  - AlphaFold ID
  - Description
- "Save Structure Info" button

**What to do:**
- Select your structure file
- Choose the format
- Optionally add PDB ID and description
- Click "Save Structure Info"
- Click "Next"

---

### 4. Step 4: Define States
**What you'll see:**
- Progress bar (Step 4 highlighted)
- "+ Add State" button at the top
- For each state (collapsible cards):
  - State name input
  - Description textarea
  - **Protein State section:**
    - Sequence textarea
    - N-terminus number input
    - C-terminus number input
    - Oligomeric state input
  - **Peptides section:**
    - "+ Add Peptide" button
    - For each peptide:
      - Data file dropdown
      - Format dropdown
      - Deuteration type dropdown
      - pH, Temperature, D% inputs
      - Remove button

**What to do:**
- Click "+ Add State" to create states
- For each state:
  - Name it (e.g., "Apo", "Ligand-bound")
  - Paste the protein sequence
  - Set N-terminus and C-terminus residue numbers
  - Click "+ Add Peptide" to add peptide data
  - Configure each peptide:
    - Select data file
    - Choose format (or auto-detect)
    - Select deuteration type
    - Enter experimental conditions (pH, temp, D%)
- Click "Next" when all states are configured

---

### 5. Step 5: Metadata
**What you'll see:**
- Progress bar (Step 5 highlighted)
- **Authors section:**
  - "+ Add Author" button
  - For each author:
    - Name input (required)
    - ORCID input
    - Affiliation input
    - Contact email input
    - Remove button
- **License dropdown** (required)
  - CC0, CC BY 4.0, CC BY-SA 4.0, MIT
- **Publication section** (optional):
  - Title input
  - DOI input
  - PMID input
  - Journal input
  - Year input
- **Dataset Description** textarea

**What to do:**
- Click "+ Add Author" and fill in author details
- Select a license (required)
- Optionally add publication information
- Optionally add dataset description
- Click "Next"

---

### 6. Step 6: Review & Generate
**What you'll see:**
- Progress bar (Step 6 highlighted)
- **Review cards** showing:
  - Files uploaded (count and list)
  - Protein identifiers
  - Structure configuration
  - States and peptide counts
  - Metadata summary
- **Validation errors box** (if any)
- **"Generate Dataset JSON" button**
- **Success box** with download button (after generation)

**What to do:**
- Review all information
- Fix any validation errors by going back to relevant steps
- Click "Generate Dataset JSON"
- Click "Download JSON" to save the file

---

## Navigation

### Progress Bar
- Shows 6 steps with numbered circles
- Active step is highlighted in blue
- Completed steps are green with checkmarks
- Click any step number to jump to that step

### Navigation Buttons
- "Previous" button (disabled on Step 1)
- "Next" button (disabled if current step incomplete)
- "Generate Dataset" button on final step

---

## Visual Design

### Color Scheme
- **Primary**: Blue (#007bff) - buttons, active elements
- **Success**: Green (#28a745) - completed steps, success messages
- **Danger**: Red (#dc3545) - remove buttons, errors
- **Warning**: Yellow (#ffc107) - warnings
- **Background**: Light gray (#f5f5f5)
- **Cards**: White with subtle shadow

### Typography
- **Headers**: Large, bold
- **Labels**: Medium weight
- **Body**: Regular weight
- **Errors/Warnings**: Smaller, colored text

### Layout
- **Max width**: 1200px centered
- **Cards**: White with rounded corners and shadow
- **Spacing**: Generous padding and margins
- **Forms**: Clear labels above inputs

---

## Interactive Elements

### Buttons
- **Primary** (blue): Main actions (Next, Generate, Save)
- **Secondary** (gray): Add actions (Add State, Add Peptide)
- **Danger** (red): Remove/Delete actions

### Inputs
- Blue border on focus
- Full-width by default
- Grid layout for related fields

### File Upload
- Drag-and-drop area with dashed border
- Changes color on hover
- Shows uploaded files in list

---

## User Experience Features

### Auto-Save
- Saves to browser localStorage every 30 seconds
- No manual save needed

### Validation
- Real-time validation on some fields
- Comprehensive validation before generation
- Clear error messages

### Progress Tracking
- Visual progress bar
- Step numbers and labels
- Easy navigation between steps

### Responsive Forms
- Adds/removes fields dynamically
- Smooth transitions
- No page reloads

---

## Tips for Users

1. **Files upload**: You can drag-and-drop or click to browse
2. **Navigation**: Click step numbers to jump between steps
3. **Dynamic forms**: Add/remove states and peptides as needed
4. **Auto-save**: Your work is automatically saved
5. **Review**: Check Step 6 for validation errors before generating
6. **Download**: Your JSON file will be named with the dataset ID

---

## Error Messages

Common errors you might see:

- "No files uploaded" - Go back to Step 1
- "No structure configured" - Complete Step 3
- "State X: Sequence is required" - Add sequence in Step 4
- "At least one author is required" - Add author in Step 5
- "License is required" - Select license in Step 5

All errors include step numbers to help you fix them quickly.
