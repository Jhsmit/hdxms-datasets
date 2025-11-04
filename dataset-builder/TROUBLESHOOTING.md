# Troubleshooting Guide

## File Upload Issues

### CORS Error
**Error**: "Cross-Origin Request Blocked: The Same Origin Policy disallows reading the remote resource"

**Solutions**:
1. **Restart the backend** - The updated CORS settings need to be loaded
   ```bash
   # Stop the backend (Ctrl+C)
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Clear browser cache**
   - Press Ctrl+Shift+Delete
   - Clear cached images and files
   - Reload the page (Ctrl+F5)

3. **Check backend is running**
   - Visit http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

4. **Verify CORS is configured**
   - Backend should show in console: "Application startup complete"
   - Check `backend/app/main.py` has `allow_origins=["*"]`

### 500 Internal Server Error

**Check backend terminal output** for the actual error:

#### Error: "Session not found"
**Solution**: The session was created in the frontend but doesn't exist in backend
- Refresh the page (F5)
- Backend will auto-create session on first upload

#### Error: "Module not found" or Import errors
**Solution**: hdxms-datasets package not accessible
```bash
cd backend
python -c "import hdxms_datasets; print('OK')"
```

If this fails:
```bash
# Make sure you're in the right directory
cd path/to/hdxms-datasets
pip install -e .
```

#### Error: "Permission denied" writing files
**Solution**: Temp directory permissions
```bash
# Windows
echo %TEMP%
# Linux/Mac
echo $TMPDIR
```

Ensure the temp directory is writable.

### Upload Appears to Work But File Not Listed

1. **Check browser console** (F12)
   - Look for JavaScript errors
   - Check Network tab for API response

2. **Check Pinia store**
   - Open Vue DevTools
   - Check store state
   - Verify file was added to `uploadedFiles`

3. **Clear localStorage**
   ```javascript
   // In browser console
   localStorage.clear()
   location.reload()
   ```

## Backend Won't Start

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Import Errors
```bash
# Reinstall dependencies
cd backend
pip install -e . --force-reinstall
```

### ModuleNotFoundError: app
Make sure you're running from the correct directory:
```bash
cd backend
uvicorn app.main:app --reload
# NOT: uvicorn main:app
```

## Frontend Won't Start

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5173
kill -9 <PID>
```

### Dependencies Not Installed
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Build Errors
```bash
# Clear Vite cache
rm -rf frontend/node_modules/.vite
npm run dev
```

## API Connection Issues

### Cannot Connect to Backend

1. **Verify backend is running**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check API URL in frontend**
   ```javascript
   // In browser console
   console.log(import.meta.env.VITE_API_URL)
   // Should be: http://localhost:8000/api or undefined (defaults to proxy)
   ```

3. **Check Vite proxy configuration**
   - File: `frontend/vite.config.ts`
   - Should proxy `/api` to `http://localhost:8000`

### 404 Not Found

**Wrong API path**
- Backend uses `/api/files/upload`
- NOT `/files/upload`

Check the API base URL in `frontend/src/services/api.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
```

## Session Issues

### Session Not Persisting

1. **Check localStorage**
   ```javascript
   // In browser console
   console.log(localStorage.getItem('hdxms-builder-draft'))
   ```

2. **Browser privacy settings**
   - Ensure cookies/localStorage are allowed
   - Try incognito mode to test

3. **Backend session expired**
   - Sessions expire after 24 hours
   - Refresh page to create new session

## Validation Issues

### "Sequence length doesn't match N-term to C-term"

The sequence length must exactly match `c_term - n_term + 1`

Example:
- N-term: 1
- C-term: 100
- Sequence must be exactly 100 amino acids long

### "State names must be unique"

Each state must have a unique name within the dataset.

### "At least one author is required"

Go to Step 5 and click "+ Add Author"

### "License is required"

Go to Step 5 and select a license from the dropdown

## Complete Reset

If all else fails, start fresh:

```bash
# 1. Stop both services (Ctrl+C)

# 2. Clear browser data
# In browser: Ctrl+Shift+Delete, clear everything

# 3. Clear backend temp files
# Windows
del /s /q %TEMP%\hdxms_*
# Linux/Mac
rm -rf /tmp/hdxms_*

# 4. Restart backend
cd backend
uvicorn app.main:app --reload

# 5. Restart frontend (new terminal)
cd frontend
npm run dev

# 6. Open fresh browser window
# Visit: http://localhost:5173
```

## Debugging Tips

### Enable Verbose Logging

**Backend**: Already prints to console
- Check terminal where uvicorn is running
- Look for errors and stack traces

**Frontend**: Open browser console (F12)
- Console tab: JavaScript errors
- Network tab: API requests/responses
- Vue DevTools: Component state

### Test API Directly

Use the interactive API docs:
1. Visit http://localhost:8000/docs
2. Try endpoints directly
3. See exact request/response

Example: Test session creation
1. Go to http://localhost:8000/docs
2. Find `POST /api/files/session`
3. Click "Try it out"
4. Click "Execute"
5. Copy the session_id from response

### Check File Paths

**Backend file storage**:
```python
# In Python console (from backend directory)
import tempfile
from pathlib import Path
print(Path(tempfile.gettempdir()) / "hdxms_builder")
```

### Check Environment

```bash
# Backend
cd backend
python --version  # Should be 3.10+
pip list | grep fastapi

# Frontend
cd frontend
node --version  # Should be 18+
npm list vue
```

## Getting More Help

If you're still stuck:

1. **Check the error message carefully**
   - Read the full error in terminal/console
   - Google the specific error message

2. **Check the documentation**
   - [README.md](README.md)
   - [INSTALLATION-CHECKLIST.md](INSTALLATION-CHECKLIST.md)
   - [backend/README.md](backend/README.md)
   - [frontend/README.md](frontend/README.md)

3. **Test with minimal example**
   - Try uploading a very small CSV file
   - Try with just one state and one peptide
   - Isolate the problem

4. **Check versions match**
   - Python 3.10+
   - Node.js 18+
   - Latest code from both backend and frontend

## Common Error Messages

### "Cannot read property 'X' of undefined"
- Frontend issue
- State not initialized
- Try refreshing page

### "File does not exist"
- Backend issue
- File wasn't saved properly
- Check temp directory exists and is writable

### "Validation failed"
- Check Step 6 Review for specific errors
- Each error tells you which step to fix

### "Network Error"
- Backend not running
- Wrong port
- Check CORS configuration

### "Timeout"
- Backend taking too long
- Large file upload
- Increase timeout in `api.ts`: `timeout: 30000`
