# HDX-MS Dataset Builder - Frontend

Vue.js 3 frontend for the HDX-MS Dataset Builder application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── wizard/
│   │   │   ├── WizardContainer.vue
│   │   │   └── steps/
│   │   │       ├── Step1FileUpload.vue
│   │   │       ├── Step2ProteinInfo.vue
│   │   │       ├── Step3Structure.vue
│   │   │       ├── Step4States.vue
│   │   │       ├── Step5Metadata.vue
│   │   │       └── Step6Review.vue
│   │   ├── forms/           # Form components (future)
│   │   └── ui/              # UI components (future)
│   ├── stores/
│   │   └── dataset.ts       # Pinia store
│   ├── services/
│   │   └── api.ts           # API client
│   ├── types/
│   │   └── dataset.ts       # TypeScript interfaces
│   ├── App.vue
│   ├── main.ts
│   └── style.css
├── package.json
└── vite.config.ts
```

## Features

### Multi-Step Wizard

The application uses a 6-step wizard interface:

1. **File Upload** - Upload data files and structure file
2. **Protein Info** - Enter protein identifiers (optional)
3. **Structure** - Configure structure file settings
4. **States** - Define protein states and peptides
5. **Metadata** - Add authors, license, and publication info
6. **Review** - Review and generate the dataset

### State Management

Uses Pinia for centralized state management. The store handles:
- Session management
- File uploads
- State/peptide CRUD operations
- Form data persistence (localStorage)
- Validation

### Auto-Save

The application automatically saves progress to localStorage every 30 seconds.

### API Integration

All backend API calls are handled through the `apiService` in `src/services/api.ts`.

## Development

### Adding New Components

1. Create component in appropriate directory under `src/components/`
2. Import and use in parent component
3. Add TypeScript interfaces in `src/types/`

### Modifying the Store

Edit `src/stores/dataset.ts` to add new state or actions.

### API Endpoints

Backend API is proxied through Vite at `/api`. Configure in `vite.config.ts`.

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000/api
```

## Testing

```bash
npm run test
```

(Tests not yet implemented in MVP)

## Linting & Formatting

```bash
npm run lint
npm run format
```
