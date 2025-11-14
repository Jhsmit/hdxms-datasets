@echo off
echo Starting HDX-MS Dataset Builder (production mode, separate servers)...

echo Starting backend...
start cmd /k "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo Starting frontend (preview mode)...
cd frontend
call npm run build
npm run preview

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:4173 (or whatever port Vite preview shows)