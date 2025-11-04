#!/bin/bash

# Start both backend and frontend in development mode

echo "Starting HDX-MS Dataset Builder in development mode..."

# Start backend in background
echo "Starting backend..."
cd backend
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "Starting frontend..."
cd ../frontend
npm run dev

# When frontend exits, kill backend
kill $BACKEND_PID
