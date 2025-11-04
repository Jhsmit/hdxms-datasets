#!/bin/bash
# Simple API test script

echo "Testing HDX-MS Dataset Builder API..."
echo ""

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/health
echo ""
echo ""

# Test 2: Create session
echo "2. Creating session..."
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/files/session | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)
echo "Session ID: $SESSION_ID"
echo ""

# Test 3: Check CORS headers
echo "3. Checking CORS headers..."
curl -i -X OPTIONS http://localhost:8000/api/files/upload \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST"
echo ""

echo "Tests complete!"
