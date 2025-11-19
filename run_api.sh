#!/bin/bash

# Start the FastAPI backend for Property Underwriter

set -euo pipefail

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"

exec uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
