#!/bin/bash

# TravelMate AI - Integrated App Startup Script
# Starts both backend and frontend with proper configuration

echo "🚀 Starting TravelMate AI - Integrated Application"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend-mcp" ] || [ ! -d "frontend-chat-v2" ]; then
    echo "❌ Error: Must run this script from the project root directory"
    exit 1
fi

# Check if backend virtual environment exists
if [ ! -d "backend-mcp/venv" ]; then
    echo "❌ Error: Backend virtual environment not found"
    echo "   Please run: cd backend-mcp && python -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend-chat-v2/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend-chat-v2
    npm install
    cd ..
fi

# Create frontend .env.local if it doesn't exist
if [ ! -f "frontend-chat-v2/.env.local" ]; then
    echo "📝 Creating frontend .env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > frontend-chat-v2/.env.local
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "🔧 Starting backend on http://localhost:8080..."
cd backend-mcp
source venv/bin/activate
uvicorn app.main:app --reload --port 8080 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Backend ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check backend.log for errors."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start frontend
echo "🎨 Starting frontend on http://localhost:3000..."
cd frontend-chat-v2
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to start..."
sleep 5

echo ""
echo "✨ TravelMate AI is running!"
echo "=================================================="
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8080"
echo "📍 API Docs: http://localhost:8080/docs"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "=================================================="

# Keep script running
wait

