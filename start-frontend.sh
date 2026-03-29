#!/bin/bash

# MTA Notifier Frontend Startup Script

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/MTA-notifier" && pwd )"

cd "$SCRIPT_DIR"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start Expo
echo "Starting MTA Notifier Frontend..."
npm start
