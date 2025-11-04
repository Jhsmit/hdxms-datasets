# Installation Checklist

Use this checklist to ensure everything is set up correctly.

## Prerequisites Check

- [ ] Python 3.10 or higher installed
  ```bash
  python --version
  ```

- [ ] Node.js 18 or higher installed
  ```bash
  node --version
  ```

- [ ] npm installed
  ```bash
  npm --version
  ```

- [ ] Git installed (optional, for cloning)
  ```bash
  git --version
  ```

## Backend Setup

- [ ] Navigate to backend directory
  ```bash
  cd dataset-builder/backend
  ```

- [ ] Install Python dependencies
  ```bash
  pip install -e .
  ```

- [ ] Verify hdxms-datasets is accessible
  ```bash
  python -c "import hdxms_datasets; print('✓ hdxms-datasets found')"
  ```

- [ ] Test FastAPI import
  ```bash
  python -c "import fastapi; print('✓ FastAPI installed')"
  ```

- [ ] Test Pydantic import
  ```bash
  python -c "import pydantic; print('✓ Pydantic installed')"
  ```

## Frontend Setup

- [ ] Navigate to frontend directory
  ```bash
  cd ../frontend  # or cd dataset-builder/frontend
  ```

- [ ] Install Node dependencies
  ```bash
  npm install
  ```

- [ ] Verify Vue is installed
  ```bash
  npm list vue
  ```

- [ ] Verify Pinia is installed
  ```bash
  npm list pinia
  ```

- [ ] Copy environment file
  ```bash
  cp .env.example .env
  ```

## Running the Application

### Backend

- [ ] Start backend server
  ```bash
  cd dataset-builder/backend
  uvicorn app.main:app --reload
  ```

- [ ] Verify backend is running
  - Open http://localhost:8000
  - Should see: `{"message": "HDX-MS Dataset Builder API", ...}`

- [ ] Check API documentation
  - Open http://localhost:8000/docs
  - Should see Swagger UI

- [ ] Test health endpoint
  ```bash
  curl http://localhost:8000/health
  ```
  - Should return: `{"status": "healthy"}`

### Frontend

- [ ] Start frontend server (in new terminal)
  ```bash
  cd dataset-builder/frontend
  npm run dev
  ```

- [ ] Verify frontend is running
  - Open http://localhost:5173
  - Should see the HDX-MS Dataset Builder interface

- [ ] Check browser console for errors
  - Press F12 in browser
  - Check Console tab
  - Should have no red errors

## Functionality Tests

### Basic Upload Test

- [ ] Click "Browse Files" under Data Files
- [ ] Select any CSV file
- [ ] File should appear in the list
- [ ] Check network tab - should see POST to `/api/files/upload`
- [ ] Should receive 200 response

### Session Test

- [ ] Open browser DevTools (F12)
- [ ] Go to Application/Storage tab
- [ ] Check localStorage
- [ ] Should see `hdxms-builder-draft` entry

### Navigation Test

- [ ] Click step numbers in progress bar
- [ ] Should be able to jump between steps
- [ ] "Previous" and "Next" buttons should work

### State Management Test

- [ ] Go to Step 4
- [ ] Click "+ Add State"
- [ ] State card should appear
- [ ] Click "+ Add Peptide"
- [ ] Peptide form should appear

## Troubleshooting

### Backend Issues

- [ ] Port 8000 not available?
  ```bash
  # Windows
  netstat -ano | findstr :8000

  # Linux/Mac
  lsof -i :8000
  ```

- [ ] Import errors?
  - Check Python version: `python --version`
  - Reinstall dependencies: `pip install -e . --force-reinstall`
  - Check hdxms-datasets path in PYTHONPATH

- [ ] CORS errors?
  - Check frontend is running on port 5173
  - Check `app/main.py` CORS settings

### Frontend Issues

- [ ] Port 5173 not available?
  ```bash
  # Windows
  netstat -ano | findstr :5173

  # Linux/Mac
  lsof -i :5173
  ```

- [ ] Dependencies not installing?
  - Clear npm cache: `npm cache clean --force`
  - Delete node_modules: `rm -rf node_modules`
  - Reinstall: `npm install`

- [ ] API calls failing?
  - Check backend is running
  - Check browser network tab for errors
  - Verify API URL in console: `import.meta.env.VITE_API_URL`

### Browser Issues

- [ ] Page not loading?
  - Clear browser cache (Ctrl+Shift+Delete)
  - Try incognito/private mode
  - Try different browser

- [ ] localStorage not working?
  - Check browser privacy settings
  - Try clearing localStorage: `localStorage.clear()` in console

## Post-Installation

- [ ] Review [QUICKSTART.md](QUICKSTART.md) for usage guide
- [ ] Review [README.md](README.md) for detailed information
- [ ] Check [MVP-SUMMARY.md](MVP-SUMMARY.md) for feature list
- [ ] Read [SCREENSHOTS.md](SCREENSHOTS.md) for visual guide

## Success Criteria

Your installation is successful if:

✅ Backend starts without errors
✅ Frontend starts without errors
✅ Can access http://localhost:8000/docs
✅ Can access http://localhost:5173
✅ Can upload files
✅ Can navigate between steps
✅ Can add states and peptides
✅ No console errors in browser

## Getting Help

If you're stuck:

1. Check error messages in terminal
2. Check browser console (F12)
3. Review the troubleshooting section above
4. Check the individual README files:
   - [backend/README.md](backend/README.md)
   - [frontend/README.md](frontend/README.md)

## Optional Enhancements

After successful installation, consider:

- [ ] Set up a code editor (VS Code recommended)
- [ ] Install Vue DevTools browser extension
- [ ] Install Python debugger
- [ ] Set up git for version control
- [ ] Configure environment variables for different environments

## Development Workflow

Once installed, your typical workflow:

1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Make changes
4. Hot reload happens automatically
5. Test in browser
6. Commit changes

## Notes

- Backend runs on port 8000
- Frontend runs on port 5173
- Sessions expire after 24 hours
- Files are stored in system temp directory
- localStorage persists between sessions
- No authentication in MVP

---

**Last Updated**: 2025-01-04
**Version**: 0.1.0 (MVP)
