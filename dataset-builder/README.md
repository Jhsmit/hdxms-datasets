# HDX-MS Dataset Builder

A web application for creating standardized HDX-MS datasets in JSON format.

## Overview

This application provides a user-friendly interface for building HDX-MS datasets that conform to the `hdxms-datasets` package format. It features:

- **Multi-step wizard interface** - 6 steps guiding users through dataset creation
- **File upload** - Support for CSV data files and PDB/mmCIF structure files
- **Dynamic forms** - Add/remove states and peptides as needed
- **Real-time validation** - Validate data against Pydantic models
- **Auto-save** - Automatically save progress to browser localStorage
- **JSON generation** - Export standardized dataset.json files

## Architecture

The application consists of two components:

1. **Backend** - FastAPI REST API for file handling and dataset generation
2. **Frontend** - Vue.js 3 SPA with Pinia state management

```
┌─────────────────────┐
│   Vue.js Frontend   │
│   (Port 5173)       │
└──────────┬──────────┘
           │ HTTP/REST
┌──────────▼──────────┐
│   FastAPI Backend   │
│   (Port 8000)       │
└─────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install -e .
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

API docs at http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## Usage

1. **Open the application** at http://localhost:5173
2. **Upload files** - Upload your HDX-MS data files and structure file
3. **Enter protein information** - Provide UniProt ID and other identifiers (optional)
4. **Configure structure** - Set PDB ID and other structure metadata
5. **Define states** - Create protein states with their peptides
   - Add multiple states
   - For each state, define the protein sequence and peptides
   - Specify deuteration types, filters, and experimental conditions
6. **Add metadata** - Enter authors, license, and publication information
7. **Review and generate** - Review your configuration and generate the JSON file

## Project Structure

```
dataset-builder/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── models/    # Request/response models
│   │   ├── services/  # Business logic
│   │   └── main.py
│   └── tests/
├── frontend/          # Vue.js frontend
│   ├── src/
│   │   ├── components/
│   │   ├── stores/
│   │   ├── services/
│   │   └── types/
│   └── public/
└── docs/
    └── dataset-builder-design.md  # Full design document
```

## Features

### MVP (v0.1.0) ✅

- [x] File upload with format detection
- [x] Multi-step wizard interface
- [x] Basic protein identifiers
- [x] Structure configuration
- [x] Dynamic state/peptide management
- [x] Metadata forms (authors, license)
- [x] JSON generation
- [x] Auto-save to localStorage
- [x] Session management

### Planned Features

- [ ] Advanced filter builder (dynamic key-value pairs)
- [ ] Data preview (CSV viewer)
- [ ] Structure viewer (3D visualization)
- [ ] Copy/duplicate states
- [ ] UniProt API integration
- [ ] Enhanced validation with suggestions
- [ ] Session persistence (database)
- [ ] ZIP package generation

## API Endpoints

### Files
- `POST /api/files/session` - Create session
- `POST /api/files/upload` - Upload file
- `DELETE /api/files/{file_id}` - Delete file
- `GET /api/files/list` - List files

### Validation
- `POST /api/validate/state` - Validate state
- `POST /api/validate/protein` - Validate protein
- `POST /api/validate/metadata` - Validate metadata

### Generation
- `POST /api/generate/json` - Generate JSON
- `POST /api/generate/package` - Generate ZIP (TODO)

## Development

See individual README files in `backend/` and `frontend/` directories for detailed development instructions.

### Running Both Services

Terminal 1 (Backend):
```bash
cd backend
uvicorn app.main:app --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

## Configuration

### Backend

Environment variables:
- `CORS_ORIGINS` - Allowed CORS origins
- `SESSION_EXPIRY_HOURS` - Session expiration (default: 24)

### Frontend

`.env` file:
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000/api)

## Data Format

The generated JSON follows the hdxms-datasets format specification. See the [design document](docs/dataset-builder-design.md) for detailed schema information.

Example output:
```json
{
  "hdx_id": "HDX_3BAE2080",
  "description": "My HDX-MS dataset",
  "states": [...],
  "structure": {...},
  "protein_identifiers": {...},
  "metadata": {...},
  "file_hash": "..."
}
```

## Troubleshooting

### Backend won't start
- Check that port 8000 is not in use
- Verify Python dependencies are installed
- Check hdxms-datasets package is accessible

### Frontend won't start
- Check that port 5173 is not in use
- Run `npm install` to ensure dependencies are installed
- Clear browser cache if seeing old versions

### File upload fails
- Check backend is running
- Verify file size is under 100MB
- Check file format is supported (.csv, .pdb, .cif)

### Session not persisting
- Check browser localStorage is enabled
- Clear localStorage if corrupted: `localStorage.clear()`

## Contributing

This is an MVP implementation. Future enhancements welcome!

## License

Same as hdxms-datasets package.

## Support

For issues and questions, please refer to:
- Design document: `docs/dataset-builder-design.md`
- Backend README: `backend/README.md`
- Frontend README: `frontend/README.md`
