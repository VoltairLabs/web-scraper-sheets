#!/bin/bash
# Setup script for the project
# This script creates a virtual environment and installs dependencies

set -e  # Exit on error

echo "=========================================="
echo "Setting up web-scraper-sheets project"
echo "=========================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if venv already exists
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists."
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        echo "Using existing virtual environment."
        echo ""
        echo "To activate it, run:"
        echo "  source venv/bin/activate"
        echo ""
        echo "Then install/update dependencies:"
        echo "  pip install -r requirements.txt"
        exit 0
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Set up environment variables:"
echo "   source setup_env.sh"
echo ""
echo "3. Run the script:"
echo "   python main.py"
echo ""
echo "Note: The virtual environment is now active in this shell."
echo "      To activate it in a new shell, run: source venv/bin/activate"

