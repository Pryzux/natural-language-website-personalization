#!/bin/bash
# Quick start script for the backend server

echo "Starting AI Website Customizer Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "Please edit backend/.env and add your OPENAI_API_KEY"
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Start server
echo "Starting server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
python main.py
