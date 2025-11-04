# HDX-MS Dataset Builder - Documentation Index

Welcome! This index helps you find the right documentation for your needs.

## 🚀 Getting Started

Start here if you're new:

1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
2. **[INSTALLATION-CHECKLIST.md](INSTALLATION-CHECKLIST.md)** - Verify your setup
3. **[SCREENSHOTS.md](SCREENSHOTS.md)** - Visual guide to using the app

## 📚 Main Documentation

### Overview
- **[README.md](README.md)** - Project overview, features, and architecture
- **[MVP-SUMMARY.md](MVP-SUMMARY.md)** - What's included in this MVP version

### Detailed Guides
- **[backend/README.md](backend/README.md)** - Backend API documentation
- **[frontend/README.md](frontend/README.md)** - Frontend development guide
- **[docs/dataset-builder-design.md](../docs/dataset-builder-design.md)** - Complete design document

## 🎯 Quick Links by Task

### "I want to install and run the application"
→ Start with [QUICKSTART.md](QUICKSTART.md)

### "I'm getting errors during installation"
→ Check [INSTALLATION-CHECKLIST.md](INSTALLATION-CHECKLIST.md) troubleshooting section

### "I don't know how to use the interface"
→ Read [SCREENSHOTS.md](SCREENSHOTS.md) for a visual walkthrough

### "I want to understand the architecture"
→ See [README.md](README.md) Architecture section

### "I want to develop new features"
→ Read [MVP-SUMMARY.md](MVP-SUMMARY.md) and [backend/README.md](backend/README.md) or [frontend/README.md](frontend/README.md)

### "I want to know what's NOT included"
→ Check [MVP-SUMMARY.md](MVP-SUMMARY.md) "What's NOT in MVP" section

### "I want to understand the design decisions"
→ Review [docs/dataset-builder-design.md](../docs/dataset-builder-design.md)

### "I want to run tests"
→ See [TESTING.md](TESTING.md) or [TESTS-SUMMARY.md](TESTS-SUMMARY.md)

### "I'm having issues with the application"
→ Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 📋 Document Descriptions

### User Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [QUICKSTART.md](QUICKSTART.md) | Fast setup and first use | 5 min |
| [SCREENSHOTS.md](SCREENSHOTS.md) | Visual guide to interface | 10 min |
| [README.md](README.md) | Complete project overview | 15 min |

### Developer Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [MVP-SUMMARY.md](MVP-SUMMARY.md) | MVP features and limitations | 10 min |
| [backend/README.md](backend/README.md) | Backend API details | 10 min |
| [frontend/README.md](frontend/README.md) | Frontend development | 10 min |
| [docs/dataset-builder-design.md](../docs/dataset-builder-design.md) | Complete design document | 30 min |

### Testing Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [TESTS-SUMMARY.md](TESTS-SUMMARY.md) | Quick test overview | 5 min |
| [TESTING.md](TESTING.md) | Complete testing guide | 15 min |
| [backend/tests/README.md](backend/tests/README.md) | Detailed test documentation | 10 min |

### Reference Documentation

| Document | Purpose |
|----------|---------|
| [INSTALLATION-CHECKLIST.md](INSTALLATION-CHECKLIST.md) | Installation verification |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Troubleshooting guide |
| [.gitignore](.gitignore) | Git ignore rules |
| [start-dev.sh](start-dev.sh) / [start-dev.bat](start-dev.bat) | Development startup scripts |

## 🗂️ File Structure Reference

```
dataset-builder/
├── INDEX.md                          # This file
├── README.md                         # Project overview
├── QUICKSTART.md                     # Quick start guide
├── MVP-SUMMARY.md                    # MVP features
├── SCREENSHOTS.md                    # Visual guide
├── INSTALLATION-CHECKLIST.md         # Setup verification
├── start-dev.sh / .bat               # Startup scripts
├── .gitignore                        # Git ignore
│
├── backend/                          # FastAPI backend
│   ├── README.md                     # Backend docs
│   ├── pyproject.toml               # Python dependencies
│   ├── app/
│   │   ├── main.py                  # FastAPI app
│   │   ├── api/                     # API endpoints
│   │   │   ├── files.py            # File operations
│   │   │   ├── validation.py       # Validation
│   │   │   └── generation.py       # JSON generation
│   │   ├── models/                  # Data models
│   │   │   └── api_models.py       # Request/response models
│   │   └── services/                # Business logic
│   │       ├── session_manager.py  # Sessions
│   │       └── file_manager.py     # File handling
│   └── tests/                       # Pytest tests (~40 tests)
│       ├── conftest.py              # Test fixtures
│       ├── test_api_basic.py        # Basic API tests
│       ├── test_session.py          # Session tests
│       ├── test_file_upload.py      # File upload tests
│       ├── test_validation.py       # Validation tests
│       └── test_file_manager.py     # Service tests
│
├── frontend/                         # Vue.js frontend
│   ├── README.md                    # Frontend docs
│   ├── package.json                 # Node dependencies
│   ├── vite.config.ts              # Vite config
│   ├── tsconfig.json               # TypeScript config
│   ├── index.html                  # HTML entry
│   ├── .env.example                # Environment template
│   └── src/
│       ├── main.ts                 # Vue app entry
│       ├── App.vue                 # Root component
│       ├── style.css               # Global styles
│       ├── components/
│       │   └── wizard/
│       │       ├── WizardContainer.vue
│       │       └── steps/           # 6 wizard steps
│       ├── stores/
│       │   └── dataset.ts          # Pinia store
│       ├── services/
│       │   └── api.ts              # API client
│       └── types/
│           └── dataset.ts          # TypeScript types
│
└── docs/
    └── dataset-builder-design.md    # Full design doc
```

## 🎓 Learning Path

### For Users

1. Read [QUICKSTART.md](QUICKSTART.md)
2. Follow installation steps
3. Try creating a test dataset
4. Reference [SCREENSHOTS.md](SCREENSHOTS.md) as needed

### For Developers

1. Read [QUICKSTART.md](QUICKSTART.md) to get it running
2. Review [MVP-SUMMARY.md](MVP-SUMMARY.md) to understand what's built
3. Read [backend/README.md](backend/README.md) OR [frontend/README.md](frontend/README.md) depending on interest
4. Study [docs/dataset-builder-design.md](../docs/dataset-builder-design.md) for complete architecture
5. Check the code and start developing!

### For Architects

1. Start with [docs/dataset-builder-design.md](../docs/dataset-builder-design.md)
2. Review [MVP-SUMMARY.md](MVP-SUMMARY.md) for current state
3. Check [README.md](README.md) for deployment considerations

## 🔧 Common Tasks

### Running the Application
```bash
# Quick start (Windows)
start-dev.bat

# Quick start (Linux/Mac)
./start-dev.sh

# Manual start
# Terminal 1:
cd backend && uvicorn app.main:app --reload

# Terminal 2:
cd frontend && npm run dev
```

### Accessing Services
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Troubleshooting
See [INSTALLATION-CHECKLIST.md](INSTALLATION-CHECKLIST.md#troubleshooting)

## 📞 Getting Help

1. Check the troubleshooting sections in:
   - [INSTALLATION-CHECKLIST.md](INSTALLATION-CHECKLIST.md#troubleshooting)
   - [backend/README.md](backend/README.md)
   - [frontend/README.md](frontend/README.md)

2. Review error messages carefully
3. Check browser console (F12)
4. Check terminal output

## 🗺️ Roadmap

See [MVP-SUMMARY.md](MVP-SUMMARY.md#next-steps-for-development) for planned features:
- Phase 1: Enhancements (v0.2.0)
- Phase 2: Infrastructure (v0.3.0)
- Phase 3: Advanced Features (v0.4.0)

## 📝 Contributing

This is an MVP. Future contributions welcome!

Areas that need work:
- Tests (none yet)
- Advanced validation
- Filter builder
- Data preview
- Structure viewer
- Better error messages

See [MVP-SUMMARY.md](MVP-SUMMARY.md#whats-not-in-mvp) for full list.

## 📄 License

Same as hdxms-datasets package.

---

**Version**: 0.1.0 (MVP)
**Last Updated**: 2025-01-04
**Status**: Functional MVP, not production-ready
