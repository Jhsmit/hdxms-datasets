@echo off
echo Starting HDX-MS Dataset Builder in development mode...

echo Starting backend...
start cmd /k "cd backend && uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak > nul

echo Starting frontend...
cd frontend
npm run dev
