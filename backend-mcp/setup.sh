#!/bin/bash

# TravelMate AI - Setup Script
# Run this to set up the backend-mcp environment

set -e  # Exit on error

echo "========================================="
echo "🚀 TravelMate AI - Backend Setup"
echo "========================================="
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3.12 --version 2>&1 || echo "not found")
if [[ $python_version == "not found" ]]; then
    echo "❌ Python 3.12 not found. Please install Python 3.12+"
    exit 1
fi
echo "✅ $python_version"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3.12 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "📝 Please copy ../.env.development to .env and add your API keys:"
    echo "   - GROQ_API_KEY"
    echo "   - STRIPE_API_KEY"
    echo "   - STRIPE_WEBHOOK_SECRET"
    echo ""
else
    echo "✅ .env file found"
    echo ""
fi

echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Initialize the database:"
echo "   python scripts/init_database.py"
echo ""
echo "3. Extract policy data (Phase 1):"
echo "   python scripts/extract_policies.py"
echo ""
echo "4. Run the MCP server:"
echo "   uvicorn app.main:app --reload --port 8080"
echo ""

