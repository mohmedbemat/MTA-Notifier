#!/bin/bash

# MTA Notifier Backend Startup Script

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
else
    echo "Virtual environment not found. Run: python3 -m venv .venv"
    exit 1
fi

# Set PYTHONPATH to current directory
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run the server
echo "Starting MTA Notifier Backend on port 8000..."
python3 app/server.py
