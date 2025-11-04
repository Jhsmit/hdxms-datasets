# Quick Start Guide

Get the HDX-MS Dataset Builder running in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Git (for cloning)

## Installation

### Step 1: Install Backend Dependencies

```bash
cd dataset-builder/backend
pip install -e .
```

This will install FastAPI, Pydantic, and other required packages.

### Step 2: Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

This will install Vue.js, Pinia, and other required packages.

## Running the Application

### Option 1: Use the Start Script (Recommended)

**On Windows:**
```bash
cd dataset-builder
start-dev.bat
```

**On Linux/Mac:**
```bash
cd dataset-builder
chmod +x start-dev.sh
./start-dev.sh
```

This will start both the backend and frontend automatically.

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd dataset-builder/backend
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd dataset-builder/frontend
npm run dev
```

## Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs

## First Steps

1. **Upload Files**
   - Click "Browse Files" or drag & drop your CSV data files
   - Upload your PDB or mmCIF structure file
   - Click "Next"

2. **Enter Protein Info** (Optional)
   - Add UniProt accession number
   - Click "Next"

3. **Configure Structure**
   - Select your structure file from dropdown
   - Add PDB ID if available
   - Click "Save Structure Info"
   - Click "Next"

4. **Define States**
   - Click "+ Add State"
   - Enter state name
   - Paste protein sequence
   - Set N-terminus and C-terminus residue numbers
   - Click "+ Add Peptide" to add peptide data
   - Select data file and configure peptide settings
   - Click "Next"

5. **Add Metadata**
   - Click "+ Add Author" and enter author information
   - Select license (required)
   - Optionally add publication information
   - Click "Next"

6. **Review & Generate**
   - Review your configuration
   - Click "Generate Dataset JSON"
   - Download the generated JSON file

## Example Dataset

Try creating a simple dataset:

1. **Files**: Upload any CSV file (for testing)
2. **Protein**: Leave empty or add "P12345"
3. **Structure**: Upload any PDB file
4. **State**:
   - Name: "Apo"
   - Sequence: "MKLLILT" (any short sequence)
   - N-term: 1, C-term: 7
   - Add one peptide with your CSV file
5. **Metadata**:
   - Author: "Your Name"
   - License: "CC0"
6. **Generate**: Click to create JSON

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000
```

### Frontend won't start
```bash
# Check if port 5173 is in use
# Windows:
netstat -ano | findstr :5173

# Linux/Mac:
lsof -i :5173
```

### Import errors
Make sure you're in the correct directory and that the hdxms-datasets package is accessible:
```bash
cd dataset-builder/backend
python -c "import hdxms_datasets; print(hdxms_datasets.__version__)"
```

## Next Steps

- Read the full [README](README.md) for more details
- Check the [design document](../docs/dataset-builder-design.md) for architecture details
- Explore the API at http://localhost:8000/docs

## Getting Help

If you encounter issues:
1. Check the error messages in the browser console (F12)
2. Check the terminal output for backend errors
3. Review the README files in backend/ and frontend/
4. Clear browser localStorage: `localStorage.clear()` in console

## Tips

- The application auto-saves every 30 seconds to localStorage
- You can navigate between steps freely
- Files are stored temporarily on the server during your session
- Click the step numbers in the progress bar to jump between steps
