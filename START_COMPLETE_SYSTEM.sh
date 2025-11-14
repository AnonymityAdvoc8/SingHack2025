#!/bin/bash

# Complete System Startup Script
# Starts both backend and frontend with taxonomy + API integration

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   TravelMate AI - Complete System Startup                     ║"
echo "║   Taxonomy + Ancileo API + Frontend                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python3 found"

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Node.js found"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} npm found"

# Check backend .env
if [ ! -f "backend-mcp/.env" ]; then
    echo -e "${RED}✗ backend-mcp/.env not found${NC}"
    echo "  Please create .env with your API keys"
    exit 1
fi
echo -e "${GREEN}✓${NC} backend-mcp/.env found"

# Check if API keys are configured
if ! grep -q "SCOOT=" backend-mcp/.env || ! grep -q "MAG=" backend-mcp/.env || ! grep -q "TRIP=" backend-mcp/.env; then
    echo -e "${YELLOW}⚠${NC}  Warning: Some Ancileo API keys may not be configured in .env"
    echo "  SCOOT, MAG, and TRIP should all be set for full functionality"
fi
echo -e "${GREEN}✓${NC} API keys configured"

# Check taxonomy file
if [ ! -f "assets/Taxonomy/Taxonomy_Hackathon.json" ]; then
    echo -e "${RED}✗ Taxonomy file not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Taxonomy file found"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Function to start backend
start_backend() {
    echo "Starting Backend..."
    cd backend-mcp
    
    # Activate venv if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start backend
    echo ""
    echo -e "${GREEN}Backend starting on http://localhost:8000${NC}"
    echo "API endpoint: http://localhost:8000/api/v1/chat/completions"
    echo ""
    uvicorn app.main:app --reload --port 8000
}

# Function to start frontend
start_frontend() {
    echo "Starting Frontend..."
    cd frontend-chat-v2
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    # Start frontend
    echo ""
    echo -e "${GREEN}Frontend starting on http://localhost:3000${NC}"
    echo ""
    npm run dev
}

# Ask user what to start
echo "What would you like to start?"
echo ""
echo "  1) Backend only (API server)"
echo "  2) Frontend only (UI)"
echo "  3) Both (recommended)"
echo "  4) Run tests first"
echo "  5) Exit"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "Starting Backend..."
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        start_backend
        ;;
    2)
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "Starting Frontend..."
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        start_frontend
        ;;
    3)
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "Starting Both Backend and Frontend..."
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        echo "This will start both services in the background."
        echo ""
        
        # Start backend in background
        cd backend-mcp
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        uvicorn app.main:app --reload --port 8000 > ../backend.log 2>&1 &
        BACKEND_PID=$!
        cd ..
        
        echo -e "${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"
        echo "  URL: http://localhost:8000"
        echo "  Logs: backend.log"
        echo ""
        
        sleep 2
        
        # Start frontend in background  
        cd frontend-chat-v2
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        npm run dev > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..
        
        echo -e "${GREEN}✓${NC} Frontend started (PID: $FRONTEND_PID)"
        echo "  URL: http://localhost:3000"
        echo "  Logs: frontend.log"
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        echo -e "${GREEN}System is running!${NC}"
        echo ""
        echo "  Frontend: http://localhost:3000"
        echo "  Backend:  http://localhost:8000"
        echo ""
        echo "To stop:"
        echo "  kill $BACKEND_PID $FRONTEND_PID"
        echo ""
        echo "Or press Ctrl+C and run:"
        echo "  killall node python3"
        echo ""
        
        # Wait
        wait
        ;;
    4)
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "Running Tests..."
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        
        cd backend-mcp
        
        echo "Test 1: Taxonomy Service"
        python3 scripts/test_taxonomy_service.py
        echo ""
        
        echo "Test 2: Ancileo API Integration"
        python3 scripts/test_ancileo_api.py
        echo ""
        
        echo "Test 3: Complete Chatbot Flow"
        python3 scripts/test_chatbot_taxonomy.py
        echo ""
        
        echo "═══════════════════════════════════════════════════════════════"
        echo -e "${GREEN}All tests complete!${NC}"
        echo "═══════════════════════════════════════════════════════════════"
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

