#!/bin/bash

# Quick Start Script for Taxonomy Extraction
# This script runs the complete extraction pipeline

echo ""
echo "========================================================================"
echo "  TAXONOMY EXTRACTION - Quick Start"
echo "========================================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"

echo "Project Root: $PROJECT_ROOT"
echo "Backend Dir: $BACKEND_DIR"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Navigate to backend directory
cd "$BACKEND_DIR" || exit 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q pypdf groq python-dotenv

echo "✓ Dependencies installed"

# Check for .env file
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo ""
    echo "⚠ WARNING: .env file not found!"
    echo "  Please create $BACKEND_DIR/.env with your GROQ_API_KEY"
    echo ""
    echo "  Example:"
    echo "  GROQ_API_KEY=your_api_key_here"
    echo ""
    exit 1
fi

echo "✓ Environment file found"

# Check for policy PDFs
POLICY_DIR="$PROJECT_ROOT/assets/Policy_Wordings"
if [ ! -d "$POLICY_DIR" ]; then
    echo ""
    echo "✗ Policy directory not found: $POLICY_DIR"
    exit 1
fi

PDF_COUNT=$(ls -1 "$POLICY_DIR"/*.pdf 2>/dev/null | wc -l)
if [ "$PDF_COUNT" -lt 3 ]; then
    echo ""
    echo "✗ Not enough policy PDFs found in $POLICY_DIR"
    echo "  Expected: 3, Found: $PDF_COUNT"
    exit 1
fi

echo "✓ Found $PDF_COUNT policy PDFs"

# Check for taxonomy file
TAXONOMY_FILE="$PROJECT_ROOT/assets/Taxonomy/Taxonomy_Hackathon.json"
if [ ! -f "$TAXONOMY_FILE" ]; then
    echo ""
    echo "✗ Taxonomy file not found: $TAXONOMY_FILE"
    exit 1
fi

echo "✓ Taxonomy file found"

echo ""
echo "========================================================================"
echo "  All Prerequisites Met!"
echo "========================================================================"
echo ""

# Ask user what they want to do
echo "What would you like to do?"
echo ""
echo "  1) Test extraction with ONE policy (recommended first)"
echo "  2) Run FULL extraction on ALL policies"
echo "  3) Exit"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "========================================================================"
        echo "  Running TEST extraction (single policy)..."
        echo "========================================================================"
        echo ""
        python3 scripts/test_single_policy.py
        ;;
    2)
        echo ""
        echo "========================================================================"
        echo "  Running FULL extraction (all policies)..."
        echo "========================================================================"
        echo ""
        python3 scripts/populate_taxonomy.py
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "  Done!"
echo "========================================================================"
echo ""

