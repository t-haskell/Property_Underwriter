#!/bin/bash

# Property Underwriter MVP - Quick Start Script

echo "🏠 Starting Property Underwriter MVP..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Start the Streamlit application
echo "Starting Streamlit application..."
echo "The app will open in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run src/app.py 