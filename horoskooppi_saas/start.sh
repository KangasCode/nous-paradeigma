#!/bin/bash

# Horoskooppi SaaS Quick Start Script

echo "🌟 Starting Horoskooppi SaaS..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file with your actual API keys:"
    echo "   - GEMINI_API_KEY"
    echo "   - STRIPE_SECRET_KEY"
    echo "   - STRIPE_PRICE_ID"
    echo "   - STRIPE_WEBHOOK_SECRET"
    echo "   - SECRET_KEY"
    echo ""
    read -p "Press Enter after updating the .env file..."
fi

# Navigate to backend directory
cd backend

# Check for Python 3.12
PYTHON_CMD="python3"
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "✅ Found Python 3.12"
elif python3 --version | grep -q "3.12"; then
    PYTHON_CMD="python3"
    echo "✅ Python 3.12 detected"
else
    echo "⚠️  WARNING: Python 3.12 not found. Using python3 (may cause flatlib installation issues)"
    echo "   For best results, install Python 3.12: brew install python@3.12"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Load environment variables
export $(cat ../.env | grep -v '^#' | xargs)

# Start the application
echo "🚀 Starting FastAPI server..."
echo "Application will be available at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py


